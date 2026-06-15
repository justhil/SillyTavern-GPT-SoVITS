/**
 * 浏览器（含 Docker 内酒馆）→ 中间件 manager.py（:3000）。
 * Genie :8000 仅在中间件 Admin / system_settings 配置。
 */

export const TTS_REMOTE_CONFIG_KEY = 'tts_plugin_remote_config';

const DEFAULT_MANAGER_PORT = 3000;

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

/** 解析完整中间件地址，如 http://192.168.1.5:3000 */
export function normalizeManagerBaseUrl(raw) {
    if (!raw || typeof raw !== 'string') return '';
    let s = raw.trim().replace(/\/+$/, '');
    if (!/^https?:\/\//i.test(s)) {
        s = `http://${s}`;
    }
    try {
        const u = new URL(s);
        if (!u.port) {
            u.port = String(DEFAULT_MANAGER_PORT);
        }
        return u.origin;
    } catch {
        return '';
    }
}

export function getConnectionConfig() {
    try {
        const raw = localStorage.getItem(TTS_REMOTE_CONFIG_KEY);
        if (!raw) {
            return { useRemote: false, ip: '', managerUrl: '', dockerMode: false };
        }
        const p = JSON.parse(raw);
        return {
            useRemote: !!p.useRemote,
            ip: p.ip || '',
            managerUrl: p.managerUrl || '',
            dockerMode: !!p.dockerMode,
        };
    } catch {
        return { useRemote: false, ip: '', managerUrl: '', dockerMode: false };
    }
}

export function setConnectionConfig(partial) {
    const cur = getConnectionConfig();
    const next = { ...cur, ...partial };
    if (next.managerUrl) {
        next.managerUrl = normalizeManagerBaseUrl(next.managerUrl);
    }
    if (next.ip) {
        next.ip = normalizeRemoteHost(next.ip);
    }
    if (next.managerUrl && !next.ip) {
        try {
            next.ip = normalizeRemoteHost(new URL(next.managerUrl).hostname);
        } catch (_) {}
    }
    if (next.ip && !next.managerUrl) {
        next.managerUrl = managerApiBase(next.ip);
    }
    if (next.useRemote || next.dockerMode) {
        next.useRemote = true;
    }
    localStorage.setItem(TTS_REMOTE_CONFIG_KEY, JSON.stringify(next));
    return next;
}

export function managerApiBase(host) {
    return `http://${host}:${DEFAULT_MANAGER_PORT}`;
}

/** @deprecated 仅取 host，请优先 resolveManagerBaseUrl */
export function resolveApiHost() {
    const base = resolveManagerBaseUrl();
    try {
        return normalizeRemoteHost(new URL(base).hostname);
    } catch {
        return '127.0.0.1';
    }
}

/**
 * 中间件完整根 URL（TTS_API、静态资源、WebSocket 同源）
 */
export function resolveManagerBaseUrl() {
    const cfg = getConnectionConfig();

    if (cfg.managerUrl) {
        const u = normalizeManagerBaseUrl(cfg.managerUrl);
        if (u) return u;
    }

    if (cfg.useRemote && cfg.ip) {
        const host = normalizeRemoteHost(cfg.ip);
        if (host) return managerApiBase(host);
    }

    const current = window.location.hostname;
    const port = window.location.port || '';

    // Docker 内酒馆：页面里的 localhost 不是宿主机，不要默认连 127.0.0.1:3000
    if (cfg.dockerMode || isLikelyDockerSillyTavern()) {
        return managerApiBase('127.0.0.1');
    }

    const isLanOrIPv6 = /^192\.168\.|^10\.|^172\.(1[6-9]|2\d|3[0-1])\.|:/.test(current);

    if (current === 'localhost' || current === '127.0.0.1') {
        return managerApiBase('127.0.0.1');
    }
    if (isLanOrIPv6) {
        let host = current;
        if (host.includes(':') && !host.startsWith('[')) {
            host = `[${host}]`;
        }
        return managerApiBase(host);
    }
    return managerApiBase('127.0.0.1');
}

/** 常见 Docker 映射：浏览器访问 localhost:8000 等，中间件在宿主机 :3000 */
export function isLikelyDockerSillyTavern() {
    const h = window.location.hostname;
    const p = window.location.port || '';
    if (h !== 'localhost' && h !== '127.0.0.1') return false;
    const dockerPorts = ['8000', '8080', '3001', '5173', '80', '443', ''];
    return dockerPorts.includes(p);
}

export function needsDockerMiddlewareSetup() {
    const cfg = getConnectionConfig();
    if (cfg.managerUrl || (cfg.useRemote && cfg.ip)) return false;
    return cfg.dockerMode || isLikelyDockerSillyTavern();
}

export function getDockerSetupHintHtml() {
    return `
        <p style="margin:0 0 8px;line-height:1.45;">
            酒馆在 <b>Docker</b> 里时，容器内的 <code>127.0.0.1:3000</code> <b>不是</b>宿主机上的中间件。
        </p>
        <p style="margin:0 0 8px;line-height:1.45;font-size:12px;color:#b2bec3;">
            请在<b>宿主机</b>运行 <code>python manager.py</code>，然后填<b>宿主机局域网 IP</b>（Windows 用 <code>ipconfig</code>，Linux/Mac 用 <code>ip addr</code>）。
        </p>
        <p style="margin:0;font-size:12px;color:#fdcb6e;">
            也可填完整地址：<code>http://192.168.x.x:3000</code>（不是 Genie 的 :8000）
        </p>
    `;
}