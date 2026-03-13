/**
/**

 * State Counter Analytics - Dynamic Tracking Script

 * 

 * Shopify Events Tracked:
 * add_to_cart - When items are added to cart
 * remove_from_cart - When items are removed from cart  
 * cart_view - When user views cart page
 * checkout_start - When user starts checkout process
 * wishlist_add - When item is added to wishlist
 * wishlist_remove - When item is removed from wishlist
 * product_view - When user views product page
 * category_view - When user views category/collection page
 * purchase - When purchase is completed
 * 
 * Usage (Simple):
 * <script src="analytics.js" data-project-id="1"></script>
 * 
 * Usage (Advanced):
 * <script 
 *   src="analytics.js" 
 *   data-project-id="1"

 *   data-api-url="http://127.0.0.1:8000/api"

 *   data-debug="true">

 * </script>


 */

(function () {


  'use strict';


  // Prevent double loading

  if (window._analyticsLoaded) {


    console.log('[Analytics] Already loaded, skipping...');

    return;

  }

  window._analyticsLoaded = true;

  // ============================================

  // AUTO-DETECT CONFIG FROM SCRIPT TAG

  // ============================================

  const currentScript = document.currentScript ||

    document.querySelector('script[src*="analytics.js"]');

  // Get project ID from script tag

  const projectId = currentScript?.getAttribute('data-project-id');

  // Get API URL (default: same domain as website)


  // Get API URL (Smart Detection)

  // 1. Prefer explicit data-api-url attribute


  // 2. If not set, derive from the script source URL
  // 3. Fallback to localhost for dev

  let defaultUrl;

  if (currentScript?.src && currentScript.src.startsWith('http')) {

    try {

      const scriptUrl = new URL(currentScript.src);

      // If script is at /api/analytics.js, base is /api/

      // We assume the script is served from the API server

      defaultUrl = scriptUrl.origin + '/api/';

      // Special handling for known production domains

      if (scriptUrl.hostname.includes('seo.prpwebs.com')) {

        defaultUrl = 'https://api.seo.prpwebs.com/api/';

      }

    } catch (e) {

      defaultUrl = 'http://127.0.0.1:8000/api/';

    }

  } else {

    defaultUrl = 'http://127.0.0.1:8000/api/';

  }

  const apiUrl = currentScript?.getAttribute('data-api-url') || defaultUrl;

  // Debug mode

  const debug = currentScript?.getAttribute('data-debug') === 'true';

  // Always log API URL detection for debugging

  console.log('[Analytics] Script src:', currentScript?.src);

  console.log('[Analytics] Default URL:', defaultUrl);

  console.log('[Analytics] Final API URL:', apiUrl);

  console.log('[Analytics] Project ID:', projectId);


  const CONFIG = {

    apiUrl: apiUrl,

    projectId: projectId,

    debug: debug

  };


  // ============================================

  // HELPER FUNCTIONS

  // ============================================

  function log(msg, data) {

    if (CONFIG.debug) {

      console.log('[Analytics]', msg, data || '');

    }
  }

  function isLikelyHuman() {


    try {
      // Only block obvious automation tools

      if (navigator.webdriver) return false;

      const ua = (navigator.userAgent || '').toLowerCase();

      // Block clear bot patterns only

      if (/(bot|spider|crawl|slurp|headless|lighthouse|puppeteer|playwright|selenium|phantom|python-requests|curl|wget)/i.test(ua)) {

        return false;

      }


      // Allow most browsers - be less strict

      return true;

    } catch (e) {

      return true; // Allow on errors to avoid blocking legit users

    }

  }


  // ============================================

  // COOKIE MANAGEMENT (StatCounter-style)

  // ============================================

  function setCookie(name, value, days) {

    const expires = new Date();

    expires.setTime(expires.getTime() + (days * 24 * 60 * 60 * 1000));

    const expiresStr = 'expires=' + expires.toUTCString();

    // SameSite=Lax, Secure, HttpOnly for security

    // Note: HttpOnly requires server-side setting, client-side can only set Secure and SameSite


    const cookieString = name + '=' + value + ';' + expiresStr + ';path=/;SameSite=Lax;Secure';

    // Only set Secure flag on HTTPS

    if (window.location.protocol === 'https:') {

      document.cookie = cookieString;

    } else {

      // For HTTP, remove Secure flag

      document.cookie = name + '=' + value + ';' + expiresStr + ';path=/;SameSite=Lax';

    }

    log('🍪 Set cookie:', name, value);


  }


  function getCookie(name) {

    const nameEQ = name + '=';

    const ca = document.cookie.split(';');

    for (let i = 0; i < ca.length; i++) {

      let c = ca[i];

      while (c.charAt(0) === ' ') c = c.substring(1, c.length);

      if (c.indexOf(nameEQ) === 0) return c.substring(nameEQ.length, c.length);

    }
    return null;

  }

  function deleteCookie(name) {

    document.cookie = name + '=;expires=Thu, 01 Jan 1970 00:00:01 UTC;path=/;SameSite=Lax;';


  }


  function generateVisitorId() {

    // Generate UUID v4-like identifier

    return 'v_' + Date.now() + '_' + Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15);

  }

  function getVisitorId() {

    // Check if user has opted out


    if (getCookie('analytics_opt_out') === 'true') {

      log('🚫 User has opted out of tracking');

      return null;

    }

    let visitorId = getCookie('visitor_id');

    if (!visitorId) {

      // First visit - generate new visitor ID

      visitorId = generateVisitorId();

      setCookie('visitor_id', visitorId, 730); // 2 years = 730 days

      log('🆕 New visitor ID generated:', visitorId);

    } else {

      log('🔄 Returning visitor ID:', visitorId);

    }
    return visitorId;

  }


  // Opt-out functions for GDPR compliance

  function optOut() {

    setCookie('analytics_opt_out', 'true', 365); // 1 year opt-out

    deleteCookie('visitor_id');

    deleteCookie('session_id');

    log('🚫 User opted out of analytics tracking');

  }

  function optIn() {

    deleteCookie('analytics_opt_out');

    log('✅ User opted in to analytics tracking');


  }


  function isOptedOut() {

    return getCookie('analytics_opt_out') === 'true';


  }


  function getSessionId() {

    // Check if user has opted out

    if (getCookie('analytics_opt_out') === 'true') {

      return null;

    }

    const SESSION_TIMEOUT = 30 * 60 * 1000; // 30 minutes

    let sessionId = getCookie('session_id');

    let lastActivity = getCookie('last_activity');


    const now = Date.now();

    // Check if session expired

    if (sessionId && lastActivity) {

      const timeSinceLastActivity = now - parseInt(lastActivity);

      if (timeSinceLastActivity < SESSION_TIMEOUT) {

        // Session still valid, update last activity (extend for 30 more minutes)

        setCookie('last_activity', now.toString(), 0.02); // ~30 minutes in days

        return sessionId;

      }

    }
    // Create new session

    sessionId = 's_' + now + '_' + Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15);

    setCookie('session_id', sessionId, 0.02); // ~30 minutes in days

    setCookie('last_activity', now.toString(), 0.02);

    log('🆕 New session ID generated:', sessionId);

    return sessionId;

  }


  function getDevice() {

    const ua = navigator.userAgent;

    // Tablet detection

    if (/(tablet|ipad|playbook|silk)|(android(?!.*mobile))/i.test(ua)) {

      return 'Tablet';

    }

    // Mobile detection

    if (/Mobile|Android|iP(hone|od)|IEMobile|BlackBerry|Kindle|Silk-Accelerated|(hpw|web)OS|Opera M(obi|ini)/i.test(ua)) {

      return 'Mobile';

    }

    // Desktop

    return 'Desktop';

  }

  function getBrowser() {

    const ua = navigator.userAgent;

    // Samsung Internet

    if (ua.includes('SamsungBrowser/')) {

      const version = ua.match(/SamsungBrowser\/([\d.]+)/);

      return version ? `Samsung Internet ${version[1]}` : 'Samsung Internet';

    }

    // UC Browser

    if (ua.includes('UCBrowser/')) {

      const version = ua.match(/UCBrowser\/([\d.]+)/);

      return version ? `UC Browser ${version[1]}` : 'UC Browser';

    }

    // Edge (must check before Chrome)

    if (ua.includes('Edg/') || ua.includes('Edge/') || ua.includes('EdgA/') || ua.includes('EdgiOS/')) {

      const version = ua.match(/Edg[A|iOS]*\/([\d.]+)/);

      return version ? `Edge ${version[1]}` : 'Edge';

    }


    // Chrome (must check before Safari)

    if (ua.includes('Chrome/') && !ua.includes('Edg')) {

      const version = ua.match(/Chrome\/([\d.]+)/);

      // Check if it's Chrome on iOS (actually Safari)

      if (ua.includes('CriOS/')) {

        const iosVersion = ua.match(/CriOS\/([\d.]+)/);

        return iosVersion ? `Chrome ${iosVersion[1]} (iOS)` : 'Chrome (iOS)';

      }

      return version ? `Chrome ${version[1]}` : 'Chrome';


    }


    // Firefox

    if (ua.includes('Firefox/') || ua.includes('FxiOS/')) {

      if (ua.includes('FxiOS/')) {

        const version = ua.match(/FxiOS\/([\d.]+)/);

        return version ? `Firefox ${version[1]} (iOS)` : 'Firefox (iOS)';

      }

      const version = ua.match(/Firefox\/([\d.]+)/);

      return version ? `Firefox ${version[1]}` : 'Firefox';

    }


    // Safari (check last because Chrome also includes Safari in UA)

    if (ua.includes('Safari/') && !ua.includes('Chrome') && !ua.includes('CriOS')) {

      const version = ua.match(/Version\/([\d.]+)/);

      return version ? `Safari ${version[1]}` : 'Safari';

    }

    // Opera

    if (ua.includes('OPR/') || ua.includes('Opera/')) {

      const version = ua.match(/OPR\/([\d.]+)/);

      return version ? `Opera ${version[1]}` : 'Opera';

    }


    // Android WebView

    if (ua.includes('wv') && ua.includes('Android')) {

      return 'Android WebView';

    }


    return 'Unknown';


  }

  function getOS() {

    const ua = navigator.userAgent;

    const platform = navigator.platform;

    // Android detection with version

    if (/Android/i.test(ua)) {

      const version = ua.match(/Android\s+([\d.]+)/i);

      if (version) {

        return `Android ${version[1]}`;

      }

      return 'Android';

    }

    // iOS detection with version

    if (/iPhone/i.test(ua)) {

      const version = ua.match(/OS\s+([\d_]+)/i);

      if (version) {

        return `iOS ${version[1].replace(/_/g, '.')}`;

      }

      return 'iOS (iPhone)';

    }

    if (/iPad/i.test(ua)) {

      const version = ua.match(/OS\s+([\d_]+)/i);

      if (version) {

        return `iPadOS ${version[1].replace(/_/g, '.')}`;


      }

      return 'iPadOS';

    }

    if (/iPod/i.test(ua)) {

      return 'iOS (iPod)';


    }


    // Windows detection

    if (/Win/i.test(platform) || /Win/i.test(ua)) {

      if (ua.includes('Windows NT 10.0')) return 'Windows 10/11';

      if (ua.includes('Windows NT 6.3')) return 'Windows 8.1';

      if (ua.includes('Windows NT 6.2')) return 'Windows 8';

      if (ua.includes('Windows NT 6.1')) return 'Windows 7';

      return 'Windows';



    }


    // macOS detection

    if (/Mac/i.test(platform) || /Mac/i.test(ua)) {

      if (ua.includes('Mac OS X')) {

        const version = ua.match(/Mac OS X (\d+[._]\d+)/);

        if (version) {

          const v = version[1].replace('_', '.');

          return `macOS ${v}`;


        }

      }

      return 'macOS';


    }


    // Linux detection

    if (/Linux/i.test(platform) || /Linux/i.test(ua)) {

      if (ua.includes('Ubuntu')) return 'Ubuntu';

      if (ua.includes('Fedora')) return 'Fedora';

      return 'Linux';

    }

    return 'Unknown';

  }


  function getScreenResolution() {

    return `${window.screen.width}x${window.screen.height}`;


  }

  function getLanguage() {

    return navigator.language || navigator.userLanguage || 'Unknown';

  }


  function getLocalTime() {

    const now = new Date();

    // Get local time in ISO format

    const localTime = now.toLocaleString('en-US', {

      year: 'numeric',

      month: '2-digit',

      day: '2-digit',

      hour: '2-digit',

      minute: '2-digit',

      second: '2-digit',

      hour12: false

    });


    // Get timezone offset

    const offset = -now.getTimezoneOffset();

    const offsetHours = Math.floor(Math.abs(offset) / 60);

    const offsetMinutes = Math.abs(offset) % 60;

    const offsetSign = offset >= 0 ? '+' : '-';

    const timezoneOffset = `${offsetSign}${String(offsetHours).padStart(2, '0')}:${String(offsetMinutes).padStart(2, '0')}`;

    return {

      local_time: now.toISOString(),

      local_time_formatted: localTime,

      timezone_offset: timezoneOffset,

      timezone_name: Intl.DateTimeFormat().resolvedOptions().timeZone

    };

  }

  function detectTrafficSource() {

    const referrer = document.referrer;

    const url = new URL(window.location.href);

    // Get UTM parameters

    const utm_source = url.searchParams.get('utm_source');

    const utm_medium = url.searchParams.get('utm_medium');

    const utm_campaign = url.searchParams.get('utm_campaign');

    // If UTM parameters exist, use them

    if (utm_source || utm_medium) {

      let source_type = 'referral';

      let source_name = utm_source || 'Unknown';

      if (utm_medium) {

        if (utm_medium.includes('cpc') || utm_medium.includes('ppc') || utm_medium.includes('paid')) {

          source_type = 'paid';


        } else if (utm_medium.includes('social')) {

          source_type = 'social';

        } else if (utm_medium.includes('email')) {

          source_type = 'email';

        } else if (utm_medium.includes('organic')) {

          source_type = 'organic';

        }

      }


      return {

        source_type: source_type,

        source_name: source_name,

        utm_source: utm_source,

        utm_medium: utm_medium,

        utm_campaign: utm_campaign

      };



    }


    // No referrer = Direct traffic



    if (!referrer || referrer === '') {


      return {

        source_type: 'direct',

        source_name: 'Direct',

        utm_source: null,

        utm_medium: null,

        utm_campaign: null

      };

    }

    try {

      const refUrl = new URL(referrer);

      const refHost = refUrl.hostname.toLowerCase();

      // Search Engines (Organic)

      const searchEngines = {

        'google': 'Google',

        'bing': 'Bing',

        'yahoo': 'Yahoo',

        'duckduckgo': 'DuckDuckGo',

        'baidu': 'Baidu',

        'yandex': 'Yandex',

        'ask': 'Ask.com'

      };

      for (const [key, name] of Object.entries(searchEngines)) {

        if (refHost.includes(key)) {

          return {

            source_type: 'organic',

            source_name: name,

            utm_source: null,

            utm_medium: null,

            utm_campaign: null

          };

        }

      }

      // Social Media

      const socialMedia = {

        'facebook': 'Facebook',

        'twitter': 'Twitter',

        'instagram': 'Instagram',

        'linkedin': 'LinkedIn',

        'pinterest': 'Pinterest',

        'reddit': 'Reddit',

        'tiktok': 'TikTok',

        'youtube': 'YouTube',

        'whatsapp': 'WhatsApp',

        'telegram': 'Telegram',

        't.co': 'Twitter',

        'fb.com': 'Facebook',

        'lnkd.in': 'LinkedIn'

      };


      for (const [key, name] of Object.entries(socialMedia)) {
        if (refHost.includes(key)) {

          return {
            source_type: 'social',
            source_name: name,
            utm_source: null,
            utm_medium: null,
            utm_campaign: null


          };

        }

      }

      // Email Clients
      if (refHost.includes('mail') || refHost.includes('outlook') || refHost.includes('gmail')) {

        return {
          source_type: 'email',
          source_name: 'Email',
          utm_source: null,
          utm_medium: null,
          utm_campaign: null

        };

      }


      // Everything else is referral

      return {
        source_type: 'referral',
        source_name: refHost,
        utm_source: null,
        utm_medium: null,

        utm_campaign: null

      };


    } catch (e) {

      // Invalid referrer URL

      return {
        source_type: 'direct',
        source_name: 'Direct',
        utm_source: null,
        utm_medium: null,
        utm_campaign: null

      };
    }


  }



  // ============================================

  // PAGE VIEW TRACKING

  // ============================================


  let visitId = null;

  let pageLoadTime = Date.now();

  let currentPage = window.location.href;


  function trackVisit() {

    // Validation

    if (!CONFIG.projectId) {

      console.error('[Analytics] ❌ Project ID not set! Add data-project-id="YOUR_ID" to script tag');

      console.error('[Analytics] Example: <script src="analytics.js" data-project-id="1"></script>');

      return;

    }

    // Check if user has opted out

    if (isOptedOut()) {

      log('🚫 User has opted out - skipping tracking');

      return;

    }

    if (!isLikelyHuman()) {

      log('🤖 Likely automated traffic, skipping analytics');

      return;


    }


    const visitorId = getVisitorId();

    const sessionId = getSessionId();

    if (!visitorId || !sessionId) {

      log('❌ Could not generate visitor or session ID');

      return;

    }
    const localTimeData = getLocalTime();
    const trafficSource = detectTrafficSource();


    const data = {

      visitor_id: visitorId,

      session_id: sessionId,

      referrer: document.referrer || 'direct',

      entry_page: window.location.href,

      device: getDevice(),

      browser: getBrowser(),

      os: getOS(),

      screen_resolution: getScreenResolution(),

      language: getLanguage(),

      timezone: localTimeData.timezone_name,

      local_time: localTimeData.local_time,

      local_time_formatted: localTimeData.local_time_formatted,

      timezone_offset: localTimeData.timezone_offset,

      traffic_source: trafficSource.source_type,

      traffic_name: trafficSource.source_name,

      utm_source: trafficSource.utm_source,

      utm_medium: trafficSource.utm_medium,

      utm_campaign: trafficSource.utm_campaign

    };

    const url = `${CONFIG.apiUrl.replace(/\/$/, '')}/analytics/${CONFIG.projectId}/track`;

    log('📤 Tracking visit...');

    log('Data:', data);


    fetch(url, {

      method: 'POST',

      headers: { 'Content-Type': 'application/json' },

      body: JSON.stringify(data)

    })

      .then(res => res.json())

      .then(result => {

        log('✅ Visit tracked!', result);

        visitId = result.visit_id;

        // Track initial page view

        trackPageView(window.location.href, document.title);

      })

      .catch(err => {


        log('❌ Error:', err.message);

      });

  }

  let currentPageViewId = null;


  function trackPageView(url, title) {

    if (!visitId) {

      log('⚠️ No visit ID, skipping page view');

      return;

    }

    // Update previous page view time before tracking new one

    if (currentPageViewId) {

      updatePageViewTimeSpent(currentPageViewId);


    }

    const data = {

      url: url || window.location.href,

      title: title || document.title,

      time_spent: 0  // Initial time is 0, will be updated on exit


    };
    const apiUrl = `${CONFIG.apiUrl.replace(/\/$/, '')}/analytics/${CONFIG.projectId}/pageview/${visitId}`;

    log('📄 Tracking page view:', data);

    fetch(apiUrl, {

      method: 'POST',

      headers: { 'Content-Type': 'application/json' },

      body: JSON.stringify(data)


    })

      .then(res => res.json())

      .then(result => {

        log('✅ Page view tracked!', result);

        // Store the pageview ID for later updates

        currentPageViewId = result.pageview_id;

      })

      .catch(err => {

        log('❌ Page view error:', err.message);

      });


    // Reset timer for next page

    pageLoadTime = Date.now();

  }

  function updatePageViewTimeSpent(pageViewId) {


    if (!pageViewId || !visitId) return;


    const timeSpent = Math.floor((Date.now() - pageLoadTime) / 1000);


    if (timeSpent < 1) return; // Don't update if less than 1 second
    const data = {
      time_spent: timeSpent
    };

    const apiUrl = `${CONFIG.apiUrl.replace(/\/$/, '')}/analytics/${CONFIG.projectId}/pageview/${visitId}/update/${pageViewId}`;

    log('⏱️ Updating time spent:', timeSpent + 's for pageview', pageViewId);

    // Use sendBeacon for reliable tracking

    if (navigator.sendBeacon) {

      const blob = new Blob([JSON.stringify(data)], { type: 'application/json' })
      navigator.sendBeacon(apiUrl, blob)

    } else {
      fetch(apiUrl, {
        method: 'PUT',

        headers: { 'Content-Type': 'application/json' },

        body: JSON.stringify(data),
        keepalive: true
      }).catch(() => { });

    } // Added closing brace here

  }

  function trackExit() {
     if (window._exitTracked) return;
  window._exitTracked = true;
    if (!visitId) return;
    // Update last page view time spent
    if (currentPageViewId) {
      updatePageViewTimeSpent(currentPageViewId);
    }
    const timeSpent = Math.floor((Date.now() - pageLoadTime) / 1000);
    const data = {
      exit_page: window.location.href,
      time_spent: timeSpent
    };
    const apiUrl = `${CONFIG.apiUrl.replace(/\/$/, '')}/analytics/${CONFIG.projectId}/exit/${visitId}`;
    log('🚪 Tracking exit:', data);
    // Use sendBeacon for reliable exit tracking
    if (navigator.sendBeacon) {
      const blob = new Blob([JSON.stringify(data)], { type: 'application/json' });
      navigator.sendBeacon(apiUrl, blob);
    } else {
      fetch(apiUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
        keepalive: true
      }).catch(() => { });
    }
  }
  function trackExitLink(url) {
    const data = {
      url: url,
      from_page: window.location.href
    };
    const apiUrl = `${CONFIG.apiUrl.replace(/\/$/, '')}/analytics/${CONFIG.projectId}/exit-link`;
    log('🔗 Tracking exit link:', data);
    // Use sendBeacon for reliable tracking
    if (navigator.sendBeacon) {
      const blob = new Blob([JSON.stringify(data)], { type: 'application/json' });
      navigator.sendBeacon(apiUrl, blob);
    } else {
      fetch(apiUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      }).catch((err) => {
        log('❌ Exit link tracking error:', err.message);
      });
    }
  }

  function setupExitLinkTracking() {

  document.addEventListener('click', (e) => {

    const link = e.target.closest('a');
    if (!link) return;

    const href = link.getAttribute('href');
    if (!href) return;

    try {

      const linkHost = new URL(href, window.location.href).hostname;
      const isExternal = linkHost !== window.location.hostname;

      if (isExternal) {
        trackExitLink(href);
        log('🔗 External link clicked:', href);
      }

    } catch (err) {
      // Ignore invalid URLs
    }

  }, true);

}

  // ============================================
  // SINGLE PAGE APPLICATION (SPA) NAVIGATION TRACKING
  // ============================================
  function trackPageNavigation() {

  const currentUrl = window.location.href;

  if (currentUrl === currentPage) return;

  trackPageView(currentUrl, document.title);

  detectProductPage();
  detectCartPage();
  detectCheckout();
  detectCategoryPage();
  
  // Run checkout detection methods on navigation
  setupCheckoutRedirectDetection();
  setupPurchaseDetection();

  currentPage = currentUrl;

}
  // ============================================
  // INITIALIZE
  // ============================================
  log('🚀 Initializing...');
  log('Project ID:', CONFIG.projectId);
  log('API URL:', CONFIG.apiUrl);
  log('Visitor ID:', getVisitorId());
  log('Session ID:', getSessionId());

  // Track visit on load
  trackVisit();
  // Track page navigation for SPAs and browser navigation
  // This will catch: back/forward buttons, refresh, hash changes, SPA navigation
  let lastUrl = window.location.href;
  // Override pushState and replaceState for SPA navigation
  const originalPushState = history.pushState;
  const originalReplaceState = history.replaceState;
  history.pushState = function() {
    originalPushState.apply(this, arguments);
    setTimeout(trackPageNavigation, 0); // Delay to allow URL to update
  };
  history.replaceState = function() {
    originalReplaceState.apply(this, arguments);
    setTimeout(trackPageNavigation, 0); // Delay to allow URL to update
  };

  // Listen for popstate (back/forward buttons)
  window.addEventListener('popstate', function() {
    setTimeout(trackPageNavigation, 100); // Small delay for browser to update
  });

  // Listen for hash changes
  window.addEventListener('hashchange', trackPageNavigation);

  // Listen for page visibility changes (handles tab switching, app backgrounding, and refresh)
  document.addEventListener('visibilitychange', function() {
    if (document.visibilityState === 'visible') {
      // Page became visible again, check if URL changed
      if (window.location.href !== lastUrl) {
        trackPageNavigation();
      }
    } else if (document.visibilityState === 'hidden') {
      // Track exit when page becomes hidden (covers refresh, tab close, etc.)
      trackExit();
    }
  });


  // Track exit on page unload (backup for older browsers)
  window.addEventListener('beforeunload', trackExit);
  window.addEventListener('pagehide', trackExit);

  // Initialize Shopify tracking
  initShopifyTracking();

  // ============================================

  // EVENT TRACKING (Shopify + Custom Events)

  // ============================================

  // General event tracking function
  function trackEvent(eventType, eventData = {}) {
    if (!visitId) {
      log('⚠️ No visit ID, skipping event:', eventType);
      return;
    }

    const data = {
      event_type: eventType,
      event_data: eventData,
      url: window.location.href,
      timestamp: Date.now()
    };

    const apiUrl = `${CONFIG.apiUrl.replace(/\/$/, '')}/analytics/${CONFIG.projectId}/event/${visitId}`;
    
    log('📊 Tracking event:', eventType, data);
    
    fetch(apiUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    })
      .then(res => res.json())
      .then(result => {
        log('✅ Event tracked!', result);
      })
      .catch(err => {
        log('❌ Event tracking error:', err.message);
      });
  }

  // Shopify Product Page Detection
  function detectProductPage() {
    if (window._lastTrackedProduct === window.location.pathname) return;
  window._lastTrackedProduct = window.location.pathname;

  if (window.location.pathname.includes('/products/')) {

    let productData = {};

    if (window.ShopifyAnalytics && window.ShopifyAnalytics.meta && window.ShopifyAnalytics.meta.product) {
      const p = window.ShopifyAnalytics.meta.product;

      productData = {
        product_id: p.id,
        product_title: p.title,
        product_vendor: p.vendor,
        product_type: p.type
      };
    }

    trackEvent('product_view', {
      ...productData,
      product_url: window.location.href,
      title: document.title
    });

  }

}

  // Shopify Cart Tracking (Add + Remove) - Advanced
  function setupAddToCartTracking() {
     if (window._statifyFetchIntercepted) return;
  window._statifyFetchIntercepted = true;
    // Method 1: Intercept fetch requests (most reliable)
    const originalFetch = window.fetch;
    window.fetch = function(...args) {
      const [url, options] = args;
      
      return originalFetch.apply(this, args).then(response => {
        // Check if this is an add to cart request
        if (url && typeof url === 'string' && url.includes('/cart/add')) {

  response.clone().json().then(cartData => {

    trackEvent('add_to_cart', {
      product_id: cartData.product_id || cartData.id,
      variant_id: cartData.variant_id,
      product_title: cartData.title,
      quantity: cartData.quantity || 1,
      price: cartData.price
    });

  }).catch(() => {

    trackEvent('add_to_cart', {
      source: 'cart_add_request',
      url: url
    });

  });

}
        // Check if this is a cart update/remove request
        if (url && typeof url === 'string' && (url.includes('/cart/change') || url.includes('/cart/update'))) {

  trackEvent('cart_updated', {
    source: 'cart_update_request',
    url: url,
    timestamp: Date.now()
  });

}
        // Check if this is a wishlist API request
        if (url && typeof url === 'string' && url.includes('/wishlist')) {
          const method = options?.method || 'GET';
          
          if (method === 'POST' || method === 'PUT') {
            trackEvent('wishlist_add', {
              url: url,
              method: method,
              timestamp: Date.now()
            });
          } else if (method === 'DELETE') {
            trackEvent('wishlist_remove', {
              url: url,
              method: method,
              timestamp: Date.now()
            });
          }
        }
        
        return response;
      });
    };

    // Method 2: Listen for form submissions (backup)
    document.addEventListener('submit', function(e) {
      const form = e.target;
      if (form.action && form.action.includes('/cart/add')) {
        log('🛒 Add to cart form detected');
        
        // Try to get product data from form
        const variantId = form.querySelector('[name="id"]')?.value;
        const quantity = form.querySelector('[name="quantity"]')?.value || '1';
        
        trackEvent('add_to_cart_form', {
          variant_id: variantId,
          quantity: quantity,
          form_action: form.action
        });
      }
    });

    
  }

  // Shopify Cart Page Detection
  function detectCartPage() {
    if (window.location.pathname === '/cart' || window.location.pathname === '/cart/') {
      trackEvent('cart_view', {
        url: window.location.href
      });
      
      // Try to fetch cart data
      fetch('/cart.js')
        .then(res => res.json())
        .then(cart => {
          trackEvent('cart_data', {
            item_count: cart.item_count,
            total_price: cart.total_price,
            currency: cart.currency,
            items: cart.items.map(item => ({
              product_id: item.product_id,
              variant_id: item.variant_id,
              title: item.title,
              quantity: item.quantity,
              price: item.price
            }))
          });
        })
        .catch(err => {
          log('Error fetching cart data:', err);
        });
    }
  }

  // Shopify Checkout Detection (Legacy - kept for compatibility)
  function detectCheckout() {
    if (
  window.location.pathname.includes('/checkout') ||
  window.location.hostname.includes('checkout')
){
      trackEvent('checkout_page_view', {
        url: window.location.href,
        step: 'checkout_page_loaded'
      });
    }
  }

  // Shopify Remove from Cart Detection
  function setupRemoveFromCartTracking() {
    // Method 1: Intercept fetch requests for cart updates
    // Note: This will be merged with the global fetch interceptor in setupAddToCartTracking

    // Method 2: Click detection for remove buttons
    document.addEventListener('click', function(e) {
      const target = e.target.closest('[href*="/cart/change"], .cart__remove, .remove-item, [data-remove-item]');
      if (target) {
        log('🗑️ Remove from cart click detected');
        
        // Try to get product info from the cart item
        const cartItem = target.closest('.cart__item, .cart-item, [data-cart-item]');
        const productId = cartItem?.getAttribute('data-product-id') || 
                          cartItem?.querySelector('[data-product-id]')?.getAttribute('data-product-id');
        const productTitle = cartItem?.querySelector('.cart__product-title, .product-title')?.textContent?.trim();
        
        trackEvent('remove_from_cart_click', {
          product_id: productId,
          product_title: productTitle,
          button_text: target.textContent?.trim()
        });
      }
    });
  }

  // Shopify Wishlist Detection
  function setupWishlistTracking() {
    // Method 1: Click detection for wishlist buttons
    document.addEventListener('click', function(e) {
      const target = e.target.closest('.wishlist-button, [data-wishlist], .add-to-wishlist, .wishlist-add');
      if (target) {
        const isInWishlist = target.classList.contains('in-wishlist') || 
                            target.getAttribute('data-in-wishlist') === 'true';
        
        // Try to get product info
        const productContainer = target.closest('.product, .product-item, [data-product-id]');
        const productId = productContainer?.getAttribute('data-product-id') || 
                         target.getAttribute('data-product-id');
        const productTitle = productContainer?.querySelector('.product-title, .product-name')?.textContent?.trim();
        const productUrl = productContainer?.querySelector('a[href*="/products/"]')?.href;
        
        if (isInWishlist) {
          trackEvent('wishlist_remove', {
            product_id: productId,
            product_title: productTitle,
            product_url: productUrl,
            button_text: target.textContent?.trim()
          });
        } else {
          trackEvent('wishlist_add', {
            product_id: productId,
            product_title: productTitle,
            product_url: productUrl,
            button_text: target.textContent?.trim()
          });
        }
      }
    });
  }

  // Shopify Checkout Button Click Tracking (Method 1 - Cart Page)
function setupCheckoutClickTracking() {

  document.addEventListener("click", function(e){

    const btn = e.target.closest(
      'button[name="checkout"], input[name="checkout"], a[href*="/checkout"], .cart__checkout-button'
    );

    if (!btn) return;
    
    // Prevent duplicate tracking
    if (btn._checkoutClicked) return;
    btn._checkoutClicked = true;
    setTimeout(() => btn._checkoutClicked = false, 1000);

    // Stop event bubbling to prevent duplicate triggers
    e.stopPropagation();

    Analytics.trackEvent("checkout_click", {
      source: "cart_page",
      page_url: window.location.href,
      button_text: btn.innerText || btn.value || "checkout"
    });

    console.log("Checkout click tracked - Method 1: Cart Page");

  }, true); // Use capture phase

}

// Method 2: Checkout Redirect Detection
function setupCheckoutRedirectDetection() {
  // Check if we're on checkout page (redirected from cart)
  if (window.location.pathname.includes("/checkout")) {
    // Only track if we came from cart (check referrer)
    const referrer = document.referrer;
    if (referrer && (referrer.includes('/cart') || referrer.includes('avpayurveda.com'))) {
      Analytics.trackEvent("checkout_start", {
        source: "checkout_redirect",
        page_url: window.location.href,
        referrer: referrer
      });
      console.log("Checkout start tracked - Method 2: Redirect Detection");
    }
  }
}

// Method 3: Purchase Detection on Thank You Page
function setupPurchaseDetection() {
  if (
    window.location.pathname.includes("thank_you") ||
    window.location.pathname.includes("thank-you") ||
    window.location.pathname.includes("/orders/")
  ) {
    // Prevent duplicate tracking
    if (!sessionStorage.getItem('statify_purchase_tracked')) {
      sessionStorage.setItem('statify_purchase_tracked', '1');
      
      Analytics.trackEvent("purchase", {
        source: "thank_you_page",
        page_url: window.location.href,
        timestamp: Date.now()
      });
      console.log("Purchase tracked - Method 3: Thank You Page");
    }
  }
}


  // Shopify Category/Collection Detection
  function detectCategoryPage() {

  if (window.location.pathname.includes('/collections/')) {

    const parts = window.location.pathname.split('/collections/');
    const categoryHandle = parts[1] ? parts[1].split('/')[0] : null;

    trackEvent('category_view', {
      category_handle: categoryHandle,
      category_url: window.location.href,
      title: document.title
    });

  }

}

  // Initialize all Shopify tracking
  function initShopifyTracking() {
    log('🛍️ Initializing Shopify tracking...');
    
    // Detect current page type
    detectProductPage();
    detectCartPage();
    detectCheckout();
    detectCategoryPage();
    
    // Setup event tracking
    setupAddToCartTracking();
    setupRemoveFromCartTracking(); 
    setupWishlistTracking();
    setupCheckoutClickTracking();
    setupCheckoutRedirectDetection();
    setupPurchaseDetection();
    setupExitLinkTracking();
   

    
    
    
    
  }

  // ============================================

  // CART ACTION TRACKING

  // ============================================

  function trackCartAction(action, productId, productName, productUrl) {

    if (!visitId) {

      log('⚠️ No visit ID, skipping cart action');

      return;

    }

    const data = {

      action: action, // 'add_to_cart' or 'remove_from_cart'

      product_id: productId,

      product_name: productName,

      product_url: productUrl,

      page_url: window.location.href

    };

    const apiUrl = `${CONFIG.apiUrl.replace(/\/$/, '')}/analytics/${CONFIG.projectId}/cart-action/${visitId}`;

    log('🛒 Tracking cart action:', data);

    fetch(apiUrl, {

      method: 'POST',

      headers: { 'Content-Type': 'application/json' },

      body: JSON.stringify(data)

    })

      .then(res => res.json())

      .then(result => {

        log('✅ Cart action tracked!', result);

      })

      .catch(err => {

        log('❌ Cart action error:', err.message);

      });

  }


  // Public API

  window.Analytics = {

    trackPageView: (url, title) => trackPageView(url, title),

    trackCartAction: (action, productId, productName, productUrl) => trackCartAction(action, productId, productName, productUrl),

    trackEvent: (eventType, eventData) => trackEvent(eventType, eventData),

    getVisitorId: getVisitorId,

    getSessionId: getSessionId,

    config: CONFIG,
  // GDPR compliance functions
    optOut: optOut,

    optIn: optIn,

    isOptedOut: isOptedOut

  };

  log('✅ Ready!');

})();



