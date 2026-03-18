import { useToastStore } from '../store/toastStore'

export function useActionFeedback() {
  const push = useToastStore((state) => state.push)

  return {
    success(message: string) {
      push({ title: message, tone: 'success' })
    },
    error(error: unknown) {
      push({
        title: error instanceof Error ? error.message : 'Действие не выполнено',
        tone: 'error'
      })
    },
    info(message: string) {
      push({ title: message, tone: 'info' })
    }
  }
}
