const API_BASE = import.meta.env.VITE_API_BASE_URL || '';

export interface ApiError {
  status: number;
  message: string;
  detail?: string;
}

export async function apiFetch<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE}${path}`;

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string> || {}),
  };

  const res = await fetch(url, {
    ...options,
    credentials: 'include',
    headers,
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    const err: ApiError = {
      status: res.status,
      message: body.detail || body.message || `HTTP ${res.status}`,
      detail: JSON.stringify(body),
    };
    throw err;
  }

  if (res.status === 204) {
    return undefined as T;
  }

  return res.json() as Promise<T>;
}

/** Fetch for multipart uploads (FormData). Browser sets Content-Type with boundary. */
export async function apiFetchMultipart<T>(
  path: string,
  formData: FormData,
  method: 'POST' | 'PUT' | 'PATCH' = 'POST'
): Promise<T> {
  const url = `${API_BASE}${path}`;

  const res = await fetch(url, {
    method,
    credentials: 'include',
    body: formData,
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    const err: ApiError = {
      status: res.status,
      message: body.detail || body.message || `HTTP ${res.status}`,
      detail: JSON.stringify(body),
    };
    throw err;
  }

  if (res.status === 204) {
    return undefined as T;
  }

  return res.json() as Promise<T>;
}
