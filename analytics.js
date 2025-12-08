/**
 * State Counter Analytics - Dynamic Tracking Script
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

(function() {
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
  const apiUrl = currentScript?.getAttribute('data-api-url') || 
    (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
      ? 'http://127.0.0.1:8000/api'  // Local development
      : window.location.origin + '/api');  // Production
  
  // Debug mode
  const debug = currentScript?.getAttribute('data-debug') === 'true';

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

  function getVisitorId() {
    let id = localStorage.getItem('visitor_id');
    if (!id) {
      id = 'v_' + Date.now() + '_' + Math.random().toString(36).substring(2, 9);
      localStorage.setItem('visitor_id', id);
    }
    return id;
  }

  function getSessionId() {
    const SESSION_TIMEOUT = 30 * 60 * 1000; // 30 minutes
    let sessionId = sessionStorage.getItem('session_id');
    let lastActivity = sessionStorage.getItem('last_activity');
    
    const now = Date.now();
    
    // Check if session expired
    if (sessionId && lastActivity) {
      const timeSinceLastActivity = now - parseInt(lastActivity);
      if (timeSinceLastActivity < SESSION_TIMEOUT) {
        // Session still valid, update last activity
        sessionStorage.setItem('last_activity', now.toString());
        return sessionId;
      }
    }
    
    // Create new session
    sessionId = 's_' + now + '_' + Math.random().toString(36).substring(2, 9);
    sessionStorage.setItem('session_id', sessionId);
    sessionStorage.setItem('last_activity', now.toString());
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

    const localTimeData = getLocalTime();
    const trafficSource = detectTrafficSource();
    
    const data = {
      visitor_id: getVisitorId(),
      session_id: getSessionId(),
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

    const url = `${CONFIG.apiUrl}/analytics/${CONFIG.projectId}/track`;
    
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

    // Update previous page view with actual time spent before tracking new one
    if (currentPageViewId) {
      updatePageViewTimeSpent(currentPageViewId);
    }

    const data = {
      url: url || window.location.href,
      title: title || document.title,
      time_spent: 0  // Initial time is 0, will be updated on exit
    };

    const apiUrl = `${CONFIG.apiUrl}/analytics/${CONFIG.projectId}/pageview/${visitId}`;
    
    log('📄 Tracking page view:', data);

    fetch(apiUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    })
    .then(res => res.json())
    .then(result => {
      log('✅ Page view tracked!', result);
      currentPageViewId = result.pageview_id;
    })
    .catch(err => {
      log('❌ Page view error:', err.message);
    });

    // Reset timer for next page
    pageLoadTime = Date.now();
  }

  function updatePageViewTimeSpent(pageViewId) {
    const timeSpent = Math.floor((Date.now() - pageLoadTime) / 1000);
    
    if (timeSpent < 1) return; // Don't update if less than 1 second

    const data = {
      time_spent: timeSpent
    };

    const apiUrl = `${CONFIG.apiUrl}/analytics/${CONFIG.projectId}/pageview/${visitId}/update/${pageViewId}`;
    
    log('⏱️ Updating time spent:', timeSpent + 's');

    // Use sendBeacon for reliable tracking
    if (navigator.sendBeacon) {
      const blob = new Blob([JSON.stringify(data)], { type: 'application/json' });
      navigator.sendBeacon(apiUrl, blob);
    } else {
      fetch(apiUrl, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
        keepalive: true
      }).catch(() => {});
    }
  }

  function trackExit() {
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

    const apiUrl = `${CONFIG.apiUrl}/analytics/${CONFIG.projectId}/exit/${visitId}`;
    
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
      }).catch(() => {});
    }
  }

  function trackExitLink(url) {
    const data = {
      url: url,
      from_page: window.location.href
    };

    const apiUrl = `${CONFIG.apiUrl}/analytics/${CONFIG.projectId}/exit-link`;
    
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
    // Track all external link clicks
    document.addEventListener('click', (e) => {
      // Find the closest anchor tag
      const link = e.target.closest('a');
      
      if (!link) return;
      
      const href = link.getAttribute('href');
      
      if (!href) return;
      
      // Check if it's an external link
      const isExternal = (
        href.startsWith('http://') || 
        href.startsWith('https://') || 
        href.startsWith('//')
      ) && !href.includes(window.location.hostname);
      
      if (isExternal) {
        trackExitLink(href);
        log('🔗 External link clicked:', href);
      }
    }, true); // Use capture phase to catch all clicks
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

  // Track exit on page unload
  window.addEventListener('beforeunload', trackExit);
  window.addEventListener('pagehide', trackExit);

  // Track page visibility changes (for mobile)
  document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'hidden') {
      trackExit();
    }
  });

  // Setup exit link tracking
  setupExitLinkTracking();

  // Public API
  window.Analytics = {
    trackPageView: (url, title) => trackPageView(url, title),
    getVisitorId: getVisitorId,
    getSessionId: getSessionId,
    config: CONFIG
  };

  log('✅ Ready!');

})();
