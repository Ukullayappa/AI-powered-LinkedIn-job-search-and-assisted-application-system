JOB_CARD_SELECTORS = [
    "li.jobs-search-results__list-item",
    "[data-occludable-job-id]",
]

JOB_TITLE_SELECTORS = [
    "a.job-card-list__title--link",
    "a.job-card-container__link",
    "a[href*='/jobs/view/']",
]

COMPANY_SELECTORS = [
    ".job-card-container__primary-description",
    ".artdeco-entity-lockup__subtitle",
]

LOCATION_SELECTORS = [
    ".job-card-container__metadata-item",
    ".artdeco-entity-lockup__caption",
]

JOB_DESCRIPTION_SELECTORS = [
    "#job-details",
    ".jobs-description__content",
    ".jobs-box__html-content",
]

EASY_APPLY_BUTTON_SELECTORS = [
    "button:has-text('Easy Apply')",
    "button[aria-label*='Easy Apply']",
]

APPLICATION_MODAL_SELECTORS = [
    ".jobs-easy-apply-modal",
    "[role='dialog']",
]