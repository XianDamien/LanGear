from types import SimpleNamespace

import pytest

from app.services.coach_runtime import CoachAgentRuntime


class FakeAsyncSessionService:
    def __init__(self):
        self.sessions = {
            ("langear-coach", "1", "thread-1"): SimpleNamespace(
                id="thread-1",
                user_id="1",
                state={"lesson_id": 10, "card_id": 20},
                last_update_time=123.0,
                events=[
                    SimpleNamespace(
                        author="user",
                        content=SimpleNamespace(
                            parts=[
                                SimpleNamespace(
                                    text=(
                                        "请基于下面的 lesson 学习上下文，用中文回答用户问题。"
                                        "\n\n上下文 JSON："
                                        '{"user_question": "原始问题"}'
                                    ),
                                ),
                            ],
                        ),
                        partial=False,
                        timestamp=1.0,
                        invocation_id="invoke-user",
                    ),
                    SimpleNamespace(
                        author="langear_lesson_coach",
                        content=SimpleNamespace(
                            parts=[
                                SimpleNamespace(text="答疑结果"),
                            ],
                        ),
                        partial=False,
                        timestamp=2.0,
                        invocation_id="invoke-coach",
                    ),
                ],
            ),
        }

    async def get_session(self, *, app_name: str, user_id: str, session_id: str):
        return self.sessions.get((app_name, user_id, session_id))

    async def create_session(self, *, app_name: str, user_id: str, session_id: str, state: dict):
        session = SimpleNamespace(
            id=session_id,
            user_id=user_id,
            state=state,
            last_update_time=None,
            events=[],
        )
        self.sessions[(app_name, user_id, session_id)] = session
        return session


@pytest.fixture
def runtime():
    instance = CoachAgentRuntime.__new__(CoachAgentRuntime)
    instance._session_service = FakeAsyncSessionService()
    return instance


@pytest.mark.asyncio
async def test_get_thread_awaits_async_session_service(runtime):
    summary = await runtime.get_thread(user_id=1, thread_id="thread-1")

    assert summary is not None
    assert summary.thread_id == "thread-1"
    assert summary.user_id == 1
    assert summary.lesson_id == 10
    assert summary.card_id == 20
    assert summary.message_count == 2


@pytest.mark.asyncio
async def test_get_thread_messages_awaits_async_session_service(runtime):
    messages = await runtime.get_thread_messages(user_id=1, thread_id="thread-1")

    assert messages == [
        {
            "author": "user",
            "content": "原始问题",
            "timestamp": 1.0,
            "invocation_id": "invoke-user",
        },
        {
            "author": "langear_lesson_coach",
            "content": "答疑结果",
            "timestamp": 2.0,
            "invocation_id": "invoke-coach",
        },
    ]


@pytest.mark.asyncio
async def test_get_or_create_session_awaits_create_session(runtime):
    session = await runtime._get_or_create_session(
        user_id=1,
        lesson_id=30,
        card_id=40,
        thread_id=None,
    )

    assert session.user_id == "1"
    assert session.state == {"lesson_id": 30, "card_id": 40}
