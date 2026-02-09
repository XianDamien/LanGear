"""FSRS adapter for spaced repetition scheduling."""

from datetime import datetime, timezone
from typing import Any

from fsrs import Card as FSRSCard
from fsrs import Rating, Scheduler, State

from app.exceptions import InvalidRatingError, SRSUpdateError
from app.models.user_card_srs import UserCardSRS


class FSRSAdapter:
    """Adapter for FSRS (Free Spaced Repetition Scheduler) algorithm.

    Handles:
    - Rating string to FSRS Rating enum conversion
    - FSRS State to database state string conversion
    - Card scheduling calculations
    - Result transformation to database format
    """

    def __init__(self):
        """Initialize FSRS scheduler with default parameters."""
        self.scheduler = Scheduler()

    def rating_from_string(self, rating_str: str) -> Rating:
        """Convert rating string to FSRS Rating enum.

        Args:
            rating_str: One of 'again', 'hard', 'good', 'easy'

        Returns:
            FSRS Rating enum value

        Raises:
            InvalidRatingError: If rating string is invalid
        """
        mapping = {
            "again": Rating.Again,
            "hard": Rating.Hard,
            "good": Rating.Good,
            "easy": Rating.Easy,
        }
        if rating_str not in mapping:
            raise InvalidRatingError()
        return mapping[rating_str]

    def state_to_string(self, state: State) -> str:
        """Convert FSRS State enum to database state string.

        Args:
            state: FSRS State enum value

        Returns:
            State string: 'new', 'learning', 'review', or 'relearning'
        """
        return state.name.lower()

    def string_to_state(self, state_str: str) -> State:
        """Convert database state string to FSRS State enum.

        Args:
            state_str: State string from database

        Returns:
            FSRS State enum value
        """
        return State[state_str.upper()]

    def schedule_card(
        self,
        current_srs: UserCardSRS | None,
        rating_str: str,
    ) -> dict[str, Any]:
        """Calculate new FSRS state based on current state and rating.

        Args:
            current_srs: Current SRS state from database (None for new cards)
            rating_str: User rating ('again', 'hard', 'good', or 'easy')

        Returns:
            Dictionary with new state:
            {
                "state": "review",
                "stability": 12.3,
                "difficulty": 5.8,
                "due": datetime(...)
            }

        Raises:
            InvalidRatingError: If rating is invalid
            SRSUpdateError: If scheduling calculation fails
        """
        try:
            # Convert rating string to enum
            rating = self.rating_from_string(rating_str)

            # Construct FSRS Card from current state
            if current_srs is None:
                # New card - use default FSRS state
                fsrs_card = FSRSCard()
            else:
                # Existing card - reconstruct from database state
                fsrs_card = FSRSCard(
                    state=self.string_to_state(current_srs.state),
                    stability=current_srs.stability,
                    difficulty=current_srs.difficulty,
                    due=current_srs.due,
                )

            # Get current time in UTC
            now = datetime.now(timezone.utc)

            # Calculate scheduling for all possible ratings
            scheduling_cards = self.scheduler.review_card(fsrs_card, now)

            # Select the result based on actual rating
            result_card = scheduling_cards[rating].card

            # Convert back to database format
            return {
                "state": self.state_to_string(result_card.state),
                "stability": result_card.stability,
                "difficulty": result_card.difficulty,
                "due": result_card.due,
            }

        except InvalidRatingError:
            raise
        except Exception as e:
            raise SRSUpdateError(f"FSRS scheduling failed: {str(e)}")
