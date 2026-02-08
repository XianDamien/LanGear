import { ElMessage } from 'element-plus'

export function useErrorToast() {
  function showError(msg: string) {
    ElMessage.error(msg)
  }

  function showSuccess(msg: string) {
    ElMessage.success(msg)
  }

  function showWarning(msg: string) {
    ElMessage.warning(msg)
  }

  return { showError, showSuccess, showWarning }
}
