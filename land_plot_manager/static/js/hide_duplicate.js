odoo.define('land_plot_manager.hide_duplicate', function (require) {
    "use strict";

    var dom = require('web.dom_ready');

    // Short phrase to match (case-insensitive)
    var MATCH_PHRASE = 'duplicate';

    // Limit how often we run the scan
    function throttle(fn, wait) {
        var last = 0;
        return function () {
            var now = Date.now();
            if (now - last > wait) {
                last = now;
                try { fn(); } catch (e) { console.error('hide_duplicate error', e); }
            }
        };
    }

    function hideDuplicateBanners() {
        try {
            // Target known notification / banner containers first (cheaper)
            var containers = document.querySelectorAll('.o_notification, .o_alert, .o_warning, .alert, .o_notification_manager');
            if (!containers || containers.length === 0) {
                // fallback: broaden the search (only when needed)
                containers = document.querySelectorAll('div, p, span');
            }
            containers.forEach(function (el) {
                try {
                    var txt = (el.textContent || '').toLowerCase();
                    if (txt.indexOf(MATCH_PHRASE) !== -1) {
                        console.info('land_plot_manager: hiding duplicate banner ->', txt.slice(0, 120));
                        // Hide the nearest logical container (prefer notification blocks)
                        var banner = el.closest('.o_notification, .o_alert, .o_warning, .alert, .o_notification_manager') || el;
                        // remove instead of hide if you prefer: banner.remove();
                        banner.style.display = 'none';
                    }
                } catch (inner) {
                    // ignore single element errors
                }
            });
        } catch (e) {
            console.warn('land_plot_manager.hide_duplicate failed', e);
        }
    }

    dom.ready.then(function () {
        console.info('land_plot_manager.hide_duplicate loaded');
        // Run once right away
        hideDuplicateBanners();

        // Observe DOM changes and throttle the handler
        try {
            var throttled = throttle(hideDuplicateBanners, 300);
            var observer = new MutationObserver(throttled);
            observer.observe(document.body, { childList: true, subtree: true });
        } catch (e) {
            console.warn('land_plot_manager: MutationObserver failed', e);
        }
    });
});
