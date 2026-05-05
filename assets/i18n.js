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

    /* index extras */
    "index-title-usage": { en: "Usage", zh: "使用" },
    "index-subtitle-detail": {
      en: "Daily insights from AI-assisted workflows. Hermes Agent sessions + WakaTime coding data.",
      zh: "AI 辅助工作流的每日洞察。Hermes Agent 会话 + WakaTime 编码数据。",
    },
    "index-reports-suffix": { en: "reports", zh: "份报告" },
    "index-weeks-suffix": { en: "weeks", zh: "周" },
    "index-overview-card-title": { en: "AI Usage Overview", zh: "AI 使用概览" },
    "index-receipt-card-title": { en: "Hermes Agent Daily Receipt", zh: "Hermes Agent 每日报告" },
    "index-dashboard-card-title": { en: "AI Overview Dashboard", zh: "AI 概览仪表盘" },
    "index-weekly-overview": { en: "Weekly Overview", zh: "周度概览" },
    "index-prompt-caching": { en: "Prompt Caching", zh: "提示缓存" },
    "index-no-receipts": { en: "No receipts yet", zh: "暂无日报" },
    "index-no-overview": { en: "AI Overview — no data", zh: "AI 概览 — 暂无数据" },
    "index-no-session-cache": { en: "Session Cache — no data", zh: "会话缓存 — 暂无数据" },

    /* shared stat labels */
    "stat-cost": { en: "Cost", zh: "费用" },
    "stat-tokens": { en: "Tokens", zh: "Token 数" },
    "stat-coding": { en: "Coding", zh: "编码" },
    "stat-prompts": { en: "Prompts", zh: "对话数" },
    "stat-sessions": { en: "Sessions", zh: "会话" },
    "stat-messages": { en: "Messages", zh: "消息数" },
    "stat-tool-calls": { en: "Tool Calls", zh: "工具调用" },
    "stat-total-tokens": { en: "Total Tokens", zh: "总 Token 数" },
    "stat-avg-ratio": { en: "Avg Ratio", zh: "平均命中率" },
    "stat-cache-read": { en: "Cache Read", zh: "缓存读取" },
    "stat-cache-write": { en: "Cache Write", zh: "缓存写入" },
    "stat-hit-ratio": { en: "Hit Ratio", zh: "命中率" },
    "stat-model-session": { en: "Model + Session", zh: "模型 + 会话" },
    "stat-ai-in": { en: "AI In", zh: "AI 输入" },

    /* overview extras */
    "overview-meta-stats": { en: "Cumulative stats", zh: "累计统计" },
    "overview-meta-days": { en: "days recorded", zh: "天记录" },
    "overview-cost-sub": { en: "USD spent on AI", zh: "AI 消费（USD）" },
    "overview-cost-combined": { en: "Token Cost ${0} + Service Cost ${1}", zh: "Token 费用 ${0} + 服务费用 ${1}" },
    "overview-token-cost": { en: "Token Cost", zh: "Token 费用" },
    "overview-service-cost": { en: "Service Cost", zh: "服务费用" },
    "overview-service-costs": { en: "Service Costs", zh: "服务费用" },
    "overview-service-costs-desc": { en: "Infrastructure & hosting services", zh: "基础设施与托管服务" },
    "overview-total-label": { en: "Total", zh: "合计" },
    "overview-ai-costs": { en: "AI Platform Costs", zh: "AI 平台费用" },
    "stat-service": { en: "Service", zh: "服务" },
    "stat-monthly-cost": { en: "Monthly Cost", zh: "月度费用" },
    "stat-total": { en: "Total", zh: "合计" },
    "overview-coding-sub": { en: "Total coding hours", zh: "总编码时长" },
    "overview-tokens-sub-prefix": { en: "Hermes", zh: "Hermes" },
    "overview-cache-section-title": { en: "Hermes Agent Cache", zh: "Hermes Agent 缓存" },
    "overview-no-cost-data": { en: "No cost data yet.", zh: "暂无费用数据。" },

    /* cache extras */
    "cache-filter-all": { en: "All", zh: "全部" },

    /* receipt extras */
    "receipt-subtitle": { en: "HERMES AGENT DAILY RECEIPT", zh: "HERMES AGENT 每日报告" },
    "receipt-section-overview": { en: "■ Overview", zh: "■ 概览" },
    "receipt-section-token": { en: "■ Token Usage", zh: "■ Token 用量" },
    "receipt-section-models": { en: "■ Models", zh: "■ 模型" },
    "receipt-section-platforms": { en: "■ Platforms", zh: "■ 平台" },
    "receipt-section-sessions": { en: "■ Sessions", zh: "■ 会话" },
    "receipt-section-tools": { en: "■ Top Tools", zh: "■ 最常用工具" },

    /* dashboard extras */
    "dash-tokens-in": { en: "in", zh: "输入" },
    "dash-tokens-out": { en: "out", zh: "输出" },
    "dash-generated-by": { en: "Generated by Hermes Agent", zh: "由 Hermes Agent 生成" },
    "dash-ai-label": { en: "AI", zh: "AI" },
    "dash-human-label": { en: "Human", zh: "人工" },

    /* ── Receipt page ── */
    "receipt-brand": { en: "HERMES AGENT", zh: "HERMES AGENT" },
    "receipt-title": { en: "DAILY RECEIPT", zh: "每日报告" },
    "receipt-overview": { en: "Overview", zh: "概览" },
    "receipt-sessions-label": { en: "Sessions", zh: "会话" },
    "receipt-messages": { en: "Messages", zh: "消息数" },
    "receipt-tool-calls": { en: "Tool Calls", zh: "工具调用" },
    "receipt-total-tokens": { en: "Total Tokens", zh: "总 Token 数" },
    "receipt-token-usage": { en: "Token Usage", zh: "Token 用量" },
    "receipt-input-tokens": { en: "Input Tokens", zh: "输入 Token" },
    "receipt-output-tokens": { en: "Output Tokens", zh: "输出 Token" },
    "receipt-total": { en: "TOTAL", zh: "合计" },
    "receipt-models": { en: "Models", zh: "模型" },
    "receipt-platforms": { en: "Platforms", zh: "平台" },
    "receipt-sessions": { en: "Sessions", zh: "会话" },
    "receipt-top-tools": { en: "Top Tools", zh: "最常用工具" },
    "receipt-no-data": { en: "No Hermes Agent activity detected.", zh: "未检测到 Hermes Agent 活动。" },
    "receipt-generated": { en: "Generated by Hermes Agent", zh: "由 Hermes Agent 生成" },

    /* ── Dashboard (AI Overview) ── */
    "dash-eyebrow": { en: "Intelligence Dashboard", zh: "智能面板" },
    "dash-title": { en: "AI Overview", zh: "AI 概览" },
    "dash-personal": { en: "Personal", zh: "个人" },
    "dash-team": { en: "Team", zh: "团队" },
    "dash-personal-activity": { en: "Personal activity", zh: "个人活动" },
    "dash-coding-time": { en: "Coding Time", zh: "编码时长" },
    "dash-total-time": { en: "Total Time", zh: "总时长" },
    "dash-ai-driven-work": { en: "AI-Driven Work", zh: "AI 驱动工作" },
    "dash-ai-driven": { en: "AI-driven", zh: "AI 驱动" },
    "dash-ai-additions": { en: "AI additions", zh: "AI 新增" },
    "dash-human-additions": { en: "Human additions", zh: "人工新增" },
    "dash-line-changes": { en: "line changes", zh: "行变更" },
    "dash-cost": { en: "Cost", zh: "费用" },
    "dash-prompts-suffix": { en: "AI prompts", zh: "AI 对话" },
    "dash-tokens": { en: "Tokens", zh: "Token 数" },
    "dash-human-followup": { en: "Human follow-up", zh: "人工跟进" },
    "dash-followup-sub": { en: "0 edits to AI-touched files", zh: "0 处对 AI 编辑文件的修改" },
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
  };

  // Auto-apply on load + wire toggle button
  function init() {
    applyLang(currentLang);
    const btn = document.getElementById("langToggle");
    if (btn && !btn.dataset.bound) {
      btn.dataset.bound = "1";
      btn.addEventListener("click", window.__toggleLang);
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
