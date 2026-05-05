/**
 * i18n for AI Usage Report (report.joyehuang.me)
 * Provides client-side English/Chinese language toggle.
 * Usage: add data-i18n="key" to text elements, data-i18n-html="key" for HTML content.
 */

(function () {
  const STORAGE_KEY = "report_lang";
  const $$ = (s, ctx) => (ctx || document).querySelectorAll(s);

  const translations = {
    /* ── Shared ── */
    "brand-name": { en: "AI Usage Report", zh: "AI 使用报告" },
    "back-home": { en: "← AI Usage Report", zh: "← AI 使用报告" },
    "footer-joye": { en: "joyehuang.me", zh: "joyehuang.me" },

    /* ── Cache page ── */
    "cache-title": { en: "Cache", zh: "缓存分析" },
    "cache-title-accent": { en: "Analysis", zh: "详情" },
    "cache-desc": {
      en: "Hermes Agent prompt caching — model-level overview & per-session breakdown",
      zh: "Hermes Agent 提示缓存 — 模型级概览与逐会话详情",
    },
    "cache-overall-label": { en: "Overall Cache Hit Ratio", zh: "整体缓存命中率" },
    "cache-overall-sub": {
      en: "{0} cached / {1} total prompt tokens",
      zh: "缓存 {0} / 总提示 {1}",
    },
    "cache-avg-label": { en: "Average Session Hit Ratio", zh: "会话平均命中率" },
    "cache-avg-sub": {
      en: "{0} sessions · overall {1}%",
      zh: "{0} 个会话 · 整体 {1}%",
    },
    "cache-read": { en: "Cache Read", zh: "缓存读取" },
    "cache-write": { en: "Cache Write", zh: "缓存写入" },
    "fresh-input": { en: "Fresh Input", zh: "新输入" },
    "cache-insight-title": { en: "About Cache Hit Ratio", zh: "关于缓存命中率" },
    "cache-insight-body-1": {
      en: "Prompt caching reduces token consumption by reusing previously computed context. A higher cache_read means more context reuse, leading to a higher hit ratio and lower costs.",
      zh: "提示缓存通过重用已有上下文来减少 token 消耗。cache_read 越高，说明越多上下文被重用，命中率越高，成本越低。",
    },
    "cache-insight-body-2": {
      en: "Current data is primarily from the Kimi API, whose OpenAI-compatible interface returns cached_tokens but not cache_write_tokens — hence Cache Write shows as 0. The Anthropic API does report cache_creation_input_tokens separately.",
      zh: "目前数据主要来自 Kimi API，其 OpenAI 兼容接口仅返回 cached_tokens 而不含 cache_write_tokens，因此 Cache Write 显示为 0。若使用 Anthropic API，则会同时记录 cache_creation_input_tokens。",
    },
    "cache-section-model": { en: "Cache Hit Ratio by Model", zh: "各模型缓存命中率" },
    "cache-section-model-table": { en: "Model Breakdown", zh: "模型明细" },
    "cache-section-sessions": { en: "All Sessions", zh: "所有会话" },
    "cache-filter-empty": {
      en: "No sessions match this filter.",
      zh: "没有符合筛选条件的会话。",
    },
    /* Table headers (cache/model) */
    "th-model": { en: "Model", zh: "模型" },
    "th-sessions": { en: "Sessions", zh: "会话数" },
    "th-input": { en: "Input", zh: "输入" },
    "th-cache-read": { en: "Cache Read", zh: "缓存读取" },
    "th-cache-write": { en: "Cache Write", zh: "缓存写入" },
    "th-output": { en: "Output", zh: "输出" },
    "th-hit-ratio": { en: "Hit Ratio", zh: "命中率" },
    "th-started": { en: "Started (Melb)", zh: "开始时间" },
    "th-msgs": { en: "Msgs", zh: "消息数" },

    /* ── Landing page (index) ── */
    "index-title": { en: "AI Usage Report", zh: "AI 使用报告" },
    "index-subtitle": {
      en: "Hermes Agent activity · WakaTime coding stats · Cost tracking",
      zh: "Hermes Agent 活动 · WakaTime 编码统计 · 费用追踪",
    },
    "index-featured-overview": { en: "Cumulative Overview", zh: "累计总览" },
    "index-featured-receipt": { en: "Latest Receipt", zh: "最新日报" },
    "index-featured-cache": { en: "Cache Analysis", zh: "缓存分析" },
    "index-featured-ai": { en: "AI Overview", zh: "AI 概览" },
    "index-archive-receipts": { en: "Daily Receipt Archive", zh: "每日日报归档" },
    "index-archive-ai": { en: "AI Overview Archive", zh: "AI 概览归档" },
    "index-no-data": { en: "No data yet", zh: "暂无数据" },

    /* ── Overview page ── */
    "overview-title": { en: "Cumulative", zh: "累计" },
    "overview-title-accent": { en: "Overview", zh: "总览" },
    "overview-desc": {
      en: "All-time Hermes Agent usage, WakaTime stats, and AI cost tracking",
      zh: "Hermes Agent 累计用量、WakaTime 统计与 AI 费用追踪",
    },
    "overview-total-tokens": { en: "Total Tokens", zh: "总 Token 数" },
    "overview-total-cost": { en: "Total Cost", zh: "总费用" },
    "overview-coding-time": { en: "Coding Time", zh: "编码时长" },
    "overview-cost-provider": { en: "Cost by Provider", zh: "各服务商费用" },
    "overview-monthly-cost": { en: "Monthly Cost", zh: "月度费用" },
    "overview-month": { en: "Month", zh: "月份" },
    "overview-cost": { en: "Cost", zh: "费用" },
    "overview-cache-section": { en: "Cache Analysis", zh: "缓存分析" },
    "overview-cache-link": { en: "→ View cache analysis", zh: "→ 查看缓存分析详情" },
    "overview-hermes-tokens": { en: "Hermes", zh: "Hermes" },
    "overview-wakatime-tokens": { en: "WakaTime", zh: "WakaTime" },
  };

  function replacer(fmt, args) {
    return fmt.replace(/\{(\d+)\}/g, (_, i) => args[parseInt(i)] ?? "");
  }

  let currentLang = localStorage.getItem(STORAGE_KEY) || "en";

  function applyLang(lang) {
    currentLang = lang;
    document.documentElement.lang = lang;

    // data-i18n elements (textContent only)
    $$("[data-i18n]").forEach((el) => {
      const key = el.dataset.i18n;
      const entry = translations[key];
      if (!entry) return;
      const text = entry[lang];
      if (text !== undefined) {
        // Handle format string arguments
        const argsStr = el.dataset.i18nArgs;
        if (argsStr) {
          try {
            const args = JSON.parse(argsStr);
            el.textContent = replacer(text, args);
          } catch {
            el.textContent = text;
          }
        } else {
          el.textContent = text;
        }
      }
    });

    // data-i18n-html elements (innerHTML)
    $$("[data-i18n-html]").forEach((el) => {
      const key = el.dataset.i18nHtml;
      const entry = translations[key];
      if (!entry) return;
      const text = entry[lang];
      if (text !== undefined) {
        const argsStr = el.dataset.i18nArgs;
        if (argsStr) {
          try {
            const args = JSON.parse(argsStr);
            el.innerHTML = replacer(text, args);
          } catch {
            el.innerHTML = text;
          }
        } else {
          el.innerHTML = text;
        }
      }
    });

    // Update toggle button text
    const btn = document.getElementById("langToggle");
    if (btn) {
      btn.textContent = lang === "en" ? "EN" : "中文";
    }

    localStorage.setItem(STORAGE_KEY, lang);
  }

  // Expose toggle function globally
  window.__toggleLang = function () {
    applyLang(currentLang === "en" ? "zh" : "en");
  
    /* ── Receipt page ── */
    "receipt-brand": { en: "HERMES AGENT", zh: "HERMES AGENT" },
    "receipt-title": { en: "DAILY RECEIPT", zh: "每日报告" },
    "receipt-total": { en: "TOTAL", zh: "合计" },
    "receipt-reasoning": { en: "Reasoning (est.)", zh: "推理（估算）" },
    "receipt-top-tools": { en: "TOP TOOLS", zh: "最常用工具" },
    "receipt-sessions": { en: "SESSIONS", zh: "会话" },
    "receipt-platforms": { en: "PLATFORMS", zh: "平台" },
    "receipt-no-data": { en: "No Hermes Agent activity detected.", zh: "未检测到 Hermes Agent 活动。" },

    /* ── Dashboard (AI Overview) ── */
    "dash-eyebrow": { en: "Intelligence Dashboard", zh: "智能面板" },
    "dash-coding-time": { en: "Total Time", zh: "总时长" },
    "dash-total-tokens": { en: "Total Tokens", zh: "总 Token 数" },
    "dash-total-prompts": { en: "Total Prompts", zh: "总对话数" },
    "dash-ai-driven": { en: "AI-driven", zh: "AI 驱动" },
    "dash-coding-activity": { en: "Coding Activity", zh: "编码活动" },
    "dash-categories": { en: "Categories", zh: "类别" },
    "dash-cost": { en: "Estimated Cost", zh: "估算费用" },
};

  // Auto-apply on load
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", () => applyLang(currentLang));
  } else {
    applyLang(currentLang);
  }
})();
