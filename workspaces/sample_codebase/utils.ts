export interface UserSession {
  userId: string;
  expiresAt: number;
}

export function parseSessionToken(raw: string): UserSession {
  return { userId: "user-1", expiresAt: Date.now() + 3600 };
}
