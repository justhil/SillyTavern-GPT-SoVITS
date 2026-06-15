/**
 * 酒馆扩展 → 中间件 manager.py 的地址（固定端口 3000）。
 * Genie TTS API（8000）只在中间件 system_settings 里配置，不要写进这里。
 */

export function normalizeRemoteHost(raw) {
    if (!raw || typeof raw !== 'string') return '';
    let s = raw.trim();
    s = s.replace(/^https?:\/\//i, '');
    const hostPart = s.split('/')[0];
    let host = hostPart;
    const lastColon = hostPart.lastIndexOf(':');
    if (lastColon > 0 && hostPart.indexOf(']') === -1) {
        const maybePort = hostPart.slice(lastColon + 1);
        if (/^\d+$/.test(maybePort)) {
            host = hostPart.slice(0, lastColon);
        }
    }
    host = host.trim();
    if (!host) return '';
    if (host.includes(':') && !host.startsWith('[')) {
        return `[${host}]`;
    }
    return host;
}

export function resolveApiHost() {
    try {
        const lsConfig = localStorage.getItem('tts_plugin_remote_config');
        const remoteConfig = lsConfig ? JSON.parse(lsConfig) : { useRemote: false, ip: '' };
        if (remoteConfig.useRemote && remoteConfig.ip) {
            const host = normalizeRemoteHost(remoteConfig.ip);
            if (host) return host;
        }
    } catch (_) {}

    const current = window.location.hostname;
    const isLanOrIPv6 = /^192\.168\.|^10\.|^172\.(1[6-9]|2\d|3[0-1])\.|:/.test(current);

    if (current === 'localhost' || current === '127.0.0.1') {
        return '127.0.0.1';
    }
    if (isLanOrIPv6) {
        if (current.includes(':') && !current.startsWith('[')) {
            return `[${current}]`;
        }
        return current;
    }
    return '127.0.0.1';
}

export function managerApiBase(host) {
    return `http://${host}:3000`;
}