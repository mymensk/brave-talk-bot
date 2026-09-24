(function () {
  const config = window.LANDING_CONFIG || {};

  // Pass UTM tags from the landing URL to the form so each response records its channel.
  function trackingParams() {
    const source = new URLSearchParams(window.location.search);
    const params = new URLSearchParams();
    for (const [key, value] of source) {
      if (key.startsWith("utm_")) params.set(key, value);
    }
    return params;
  }

  function mountForm() {
    const container = document.querySelector("[data-form]");
    if (!container || !config.yandexFormId) return;

    const params = trackingParams();
    params.set("iframe", "1");
    const formUrl = `https://forms.yandex.ru/u/${encodeURIComponent(config.yandexFormId)}/`;

    const iframe = document.createElement("iframe");
    iframe.src = `${formUrl}?${params}`;
    iframe.name = `ya-form-${config.yandexFormId}`;
    iframe.title = "Анкета";
    iframe.loading = "lazy";

    const fallback = document.createElement("p");
    fallback.className = "form__fallback";
    const link = document.createElement("a");
    link.href = `${formUrl}?${trackingParams()}`;
    link.target = "_blank";
    link.rel = "noopener";
    link.textContent = "Открыть анкету в новой вкладке";
    fallback.append("Форма не загрузилась? ", link);

    container.replaceChildren(iframe, fallback);

    // Yandex Forms script resizes the iframe to the form height.
    const embed = document.createElement("script");
    embed.src = "https://forms.yandex.ru/_static/embed.js";
    document.body.append(embed);
  }

  function mountMetrika() {
    const id = Number(config.metrikaId);
    if (!id) return;
    (function (m, e, t, r, i, k, a) {
      m[i] = m[i] || function () { (m[i].a = m[i].a || []).push(arguments); };
      m[i].l = 1 * new Date();
      k = e.createElement(t); a = e.getElementsByTagName(t)[0];
      k.async = 1; k.src = r; a.parentNode.insertBefore(k, a);
    })(window, document, "script", "https://mc.yandex.ru/metrika/tag.js", "ym");
    window.ym(id, "init", { clickmap: true, trackLinks: true, accurateTrackBounce: true });

    document.querySelectorAll('a[href="#survey"]').forEach((a) =>
      a.addEventListener("click", () => window.ym(id, "reachGoal", "cta_click")),
    );
  }

  mountForm();
  mountMetrika();
})();
