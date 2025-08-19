"""
Playwright配置文件
包含浏览器自动化和MOE网站访问的配置
"""

PLAYWRIGHT_CONFIG = {
    "headless": True,
    "timeout": 30000,
    "viewport": {"width": 1920, "height": 1080},
    "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "locale": "en-SG",
    "timezone_id": "Asia/Singapore",
    "extra_http_headers": {
        "Accept-Language": "en-SG,en;q=0.9"
    }
}

MOE_URLS = {
    "base": "https://www.moe.gov.sg",
    "p1_registration": "/primary/p1-registration",
    "vacancies": "/primary/p1-registration/vacancies-and-balloting",
    "past_data": "/primary/p1-registration/past-vacancies-and-balloting-data",
    "registration_phases": "/primary/p1-registration/registration-phases-key-dates",
    "results": "/primary/p1-registration/results"
}

SCRAPING_CONFIG = {
    "request_delay": 2000,  # 2秒延迟
    "retry_attempts": 3,
    "retry_delay": 5000,  # 5秒重试延迟
    "selectors": {
        "school_table": "table",
        "vacancy_data": "[data-testid='vacancy']",
        "phase_info": ".phase-info",
        "balloting_results": ".balloting-data"
    }
}

BROWSER_OPTIONS = {
    "chromium": {
        "args": [
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--disable-web-security",
            "--disable-features=VizDisplayCompositor"
        ]
    }
}