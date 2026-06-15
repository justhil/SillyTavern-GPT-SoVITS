// static/js/api.js
import { getConnectionConfig } from './connection_host.js';

function middlewareApiKey() {
    try {
        const k = getConnectionConfig().apiKey;
        return k && String(k).trim() ? String(k).trim() : '';
    } catch {
        return '';
    }
}

function authHeaders(extra = {}) {
    const h = { ...extra };
    const key = middlewareApiKey();
    if (key) h['X-TTS-API-Key'] = key;
    return h;
}

export const TTS_API = {
    baseUrl: "",

    init: function (url) {
        this.baseUrl = url;
        console.log("🔵 [API] 服务地址已设定:", this.baseUrl);
    },

    _url: function (endpoint) {
        return `${this.baseUrl}${endpoint}`;
    },

    async _fetch(endpoint, options = {}) {
        const headers = authHeaders(options.headers || {});
        return fetch(this._url(endpoint), { ...options, headers });
    },

    async ping() {
        const controller = new AbortController();
        const t = setTimeout(() => controller.abort(), 3000);
        try {
            const res = await this._fetch('/ping', { signal: controller.signal });
            clearTimeout(t);
            return res.ok;
        } catch {
            clearTimeout(t);
            return false;
        }
    },

    async getData() {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 8000);

        try {
            const res = await this._fetch('/get_data', {
                signal: controller.signal
            });
            clearTimeout(timeoutId);

            if (!res.ok) throw new Error("API Connection Failed");
            return await res.json();
        } catch (error) {
            clearTimeout(timeoutId);
            if (error.name === 'AbortError') {
                throw new Error("连接超时 (3秒)");
            }
            throw error;
        }
    },

    async updateSettings(payload) {
        await this._fetch('/update_settings', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
    },
    //TODO 修改为V2端口
    async checkCache(params) {
        const queryParams = { ...params, check_only: "true" };
        const query = new URLSearchParams(queryParams).toString();
        const res = await this._fetch(`/tts_proxy?${query}`, {
            cache: 'no-store'
        });

        if (!res.ok) {
            // 尝试解析后端返回的详细错误信息
            let errorMsg = `缓存检查失败 (${res.status})`;
            try {
                const errorData = await res.json();
                if (errorData.detail) {
                    errorMsg = errorData.detail;
                }
            } catch (parseError) {
                // JSON 解析失败,使用默认错误信息
                console.warn("无法解析错误响应:", parseError);
            }
            throw new Error(errorMsg);
        }

        const data = await res.json();
        return {
            cached: data.cached === true,
            filename: data.filename
        };
    },
    //TODO 修改为V2端口
    async generateAudio(params) {
        const queryParams = { ...params, streaming_mode: "false" };
        const query = new URLSearchParams(queryParams).toString();
        const res = await this._fetch(`/tts_proxy?${query}`, {
            cache: 'no-store'
        });

        if (!res.ok) {
            // 尝试解析后端返回的详细错误信息
            let errorMsg = `TTS 生成失败 (${res.status})`;
            try {
                const errorData = await res.json();
                if (errorData.detail) {
                    errorMsg = errorData.detail;
                }
            } catch (parseError) {
                // JSON 解析失败,使用默认错误信息
                console.warn("无法解析错误响应:", parseError);
            }
            throw new Error(errorMsg);
        }

        const filename = res.headers.get("X-Audio-Filename");
        return {
            blob: await res.blob(),
            filename: filename
        };
    },

    async switchWeights(endpoint, path) {
        const res = await this._fetch(`/${endpoint}?weights_path=${path}`);

        if (!res.ok) {
            // 尝试解析后端返回的详细错误信息
            let errorMsg = `权重切换失败 (${res.status})`;
            try {
                const errorData = await res.json();
                if (errorData.detail) {
                    errorMsg = errorData.detail;
                }
            } catch (parseError) {
                // JSON 解析失败,使用默认错误信息
                console.warn("无法解析错误响应:", parseError);
            }
            throw new Error(errorMsg);
        }
    },

    // === 缓存管理 ===
    async deleteCache(filename) {
        // 构造查询参数 ?filename=xxx
        const query = new URLSearchParams({ filename: filename }).toString();

        // 发送请求
        const res = await this._fetch(`/delete_cache?${query}`);
        return await res.json();
    },

    // === 收藏夹管理 ===
    async getFavorites() {
        const res = await this._fetch('/get_favorites');
        return await res.json();
    },

    async addFavorite(payload) {
        // payload 格式: { text, audio_url, char_name, context: [...] }
        const res = await this._fetch('/add_favorite', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        return await res.json();
    },

    async deleteFavorite(id) {
        await this._fetch('/delete_favorite', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ id: id })
        });
    },

    async getMatchedFavorites(payload) {
        const res = await this._fetch('/get_matched_favorites', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        return await res.json();
    },
    // ===========================================
    // 【新增】管理类 API (原本散落在 ui_legacy.js 里)
    // ===========================================

    /**
     * 绑定角色到模型文件夹
     */
    async bindCharacter(charName, modelFolder) {
        const res = await this._fetch('/bind_character', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ char_name: charName, model_folder: modelFolder })
        });
        if (!res.ok) throw new Error("Bind failed");
    },

    /**
     * 解绑角色
     */
    async unbindCharacter(charName) {
        const res = await this._fetch('/unbind_character', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ char_name: charName })
        });
        if (!res.ok) throw new Error("Unbind failed");
    },

    /**
     * 创建新的模型文件夹
     */
    async createModelFolder(folderName) {
        const res = await this._fetch('/create_model_folder', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ folder_name: folderName })
        });
        if (!res.ok) throw new Error("Create folder failed");
    },

    // ===========================================
    // 【新增】说话人管理 API
    // ===========================================

    /**
     * 获取指定对话的所有说话人
     */
    async getSpeakers(chatBranch) {
        const res = await this._fetch(`/api/speakers/${encodeURIComponent(chatBranch)}`);
        if (!res.ok) throw new Error("Get speakers failed");
        return await res.json();
    },

    /**
     * 更新对话的说话人列表
     */
    async updateSpeakers(payload) {
        // payload 格式: { chat_branch, speakers, mesid }
        const res = await this._fetch('/api/speakers/update', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        if (!res.ok) throw new Error("Update speakers failed");
        return await res.json();
    },

    /**
     * 批量初始化说话人记录 (用于旧对话扫描)
     */
    async batchInitSpeakers(speakersData) {
        // speakersData 格式: [{ chat_branch, speakers, mesid }, ...]
        const res = await this._fetch('/api/speakers/batch_init', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ speakers_data: speakersData })
        });
        if (!res.ok) throw new Error("Batch init speakers failed");
        return await res.json();
    },

    // ===========================================
    // 【新增】自动来电管理 API
    // ===========================================

    /**
     * 获取角色最新的自动来电记录
     */
    async getLatestAutoCall(charName) {
        const res = await this._fetch(`/api/phone_call/auto/latest/${encodeURIComponent(charName)}`);
        if (!res.ok) throw new Error("Get latest auto call failed");
        return await res.json();
    },

    /**
     * 获取角色的来电历史记录
     */
    async getAutoCallHistory(charName, limit = 50) {
        const res = await this._fetch(`/api/phone_call/auto/history/${encodeURIComponent(charName)}?limit=${limit}`);
        if (!res.ok) throw new Error("Get auto call history failed");
        return await res.json();
    },

    /**
     * 根据对话分支获取来电历史记录
     */
    async getAutoCallHistoryByChatBranch(chatBranch, limit = 50) {
        const res = await this._fetch(`/api/phone_call/auto/history_by_branch/${encodeURIComponent(chatBranch)}?limit=${limit}`);
        if (!res.ok) throw new Error("Get auto call history by branch failed");
        return await res.json();
    },

    /**
     * 根据指纹列表获取来电历史记录（支持跨分支匹配）
     */
    async getAutoCallHistoryByFingerprints(fingerprints, limit = 50) {
        const res = await this._fetch('/api/phone_call/auto/history_by_fingerprints', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ fingerprints, limit })
        });
        if (!res.ok) throw new Error("Get auto call history by fingerprints failed");
        return await res.json();
    }
};
