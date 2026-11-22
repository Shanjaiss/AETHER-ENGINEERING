export function renderUserName(user: {name: string, nickname?: string}): string {
    return (user.nickname || user.name || 'Anonymous').toUpperCase();
}
