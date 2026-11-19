interface ApiEnvelope<T> {
  success: true
  data: T
}

interface ApiErrorBody {
  code?: string
  message?: string
  details?: {
    fields?: Array<{ field: string; message: string }>
  }
}

interface ApiErrorResponse {
  success?: false
  error?: ApiErrorBody
  detail?: string | Array<{ msg?: string }>
  message?: string
  code?: string
}

const isApiEnvelope = <T>(value: unknown): value is ApiEnvelope<T> => {
  return typeof value === 'object' && value !== null &&
    'success' in value && value.success === true && 'data' in value
}

export const useApi = () => {
  const config = useRuntimeConfig().public
  const authStore = useAuthStore()

  const request = async <T>(path: string, options: Parameters<typeof $fetch>[1] = {}): Promise<T> => {
    const headers = new Headers(options.headers as HeadersInit | undefined)
    if (authStore.token) {
      headers.set('Authorization', `Bearer ${authStore.token}`)
    }

    const response = await $fetch<unknown>(`${config.apiBaseUrl}${path}`, {
      ...options,
      headers
    })

    if (!isApiEnvelope<T>(response)) {
      throw new Error('La API devolvió una respuesta con un formato inesperado.')
    }

    return response.data
  }

  return { request }
}

export function extractApiError(err: unknown): { status: number; code: string; message: string } {
  const error = typeof err === 'object' && err !== null ? err as Record<string, unknown> : {}
  const response = typeof error.response === 'object' && error.response !== null
    ? error.response as Record<string, unknown>
    : {}
  const status = Number(response.status ?? error.statusCode ?? error.status ?? 500)
  const data = (error.data ?? response._data) as ApiErrorResponse | undefined
  const apiError = data?.error
  const code = apiError?.code ??
    data?.code ??
    (status === 403 ? 'FORBIDDEN' : status === 422 ? 'VALIDATION_ERROR' : status === 400 ? 'BAD_REQUEST' : 'API_ERROR')
  const fieldMessages = apiError?.details?.fields?.map(({ field, message }) => `${field}: ${message}`)
  const detail = Array.isArray(data?.detail)
    ? data.detail.map((item) => item.msg).filter(Boolean).join(', ')
    : data?.detail
  const message = apiError?.message ??
    (fieldMessages?.length ? fieldMessages.join('; ') : undefined) ??
    detail ??
    data?.message ??
    (typeof error.message === 'string' ? error.message : undefined) ??
    'Error inesperado al comunicarse con el servidor.'

  return { status, code, message }
}
