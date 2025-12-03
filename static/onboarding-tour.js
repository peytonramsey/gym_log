/**
 * FitGlyph Onboarding Tour
 * Shows first-time users how to use the app
 */

class OnboardingTour {
    constructor() {
        this.currentStep = 0;
        this.steps = [
            {
                title: "Welcome to FitGlyph! 💪",
                content: "Let's take a quick tour to show you around. This will only take a minute!",
                element: null,
                position: "center"
            },
            {
                title: "Your Home Dashboard",
                content: "Here you can see your workout calendar, today's nutrition, consistency stats, and quick access to all features.",
                element: ".welcome-text",
                position: "bottom"
            },
            {
                title: "Bottom Navigation",
                content: "Use these tabs to navigate between Home, Log Workout, Nutrition, History, and Progress tracking.",
                element: ".bottom-nav",
                position: "top"
            },
            {
                title: "Log Your Workouts",
                content: "Click 'Log' to record your exercises, sets, reps, and weight. You can even track individual sets and rest times!",
                element: "a[href='/log']",
                position: "top",
                highlightBottom: true
            },
            {
                title: "Track Your Nutrition",
                content: "Monitor your daily calories and macros. Search for foods using the USDA database or add custom items.",
                element: "a[href='/nutrition']",
                position: "top",
                highlightBottom: true
            },
            {
                title: "AI Weight Predictions",
                content: "Our ML model learns from your workout history to suggest optimal weights for progressive overload!",
                element: ".stat-card",
                position: "bottom"
            },
            {
                title: "Settings & Customization",
                content: "Access settings to change your theme, weight units, and manage your account.",
                element: "a[href='/settings']",
                position: "bottom"
            },
            {
                title: "You're All Set! 🎉",
                content: "Ready to start your fitness journey? Click 'Log Workout' to record your first session!",
                element: null,
                position: "center"
            }
        ];
    }

    start(force = false) {
        // Check if user has already seen the tour (unless forced restart)
        if (!force && localStorage.getItem('onboardingComplete') === 'true') {
            return;
        }

        // Check if user is on login/register pages (tour should not run there)
        const isAuthPage = window.location.pathname === '/login' ||
                          window.location.pathname === '/register';
        if (isAuthPage && !force) {
            return;
        }

        this.currentStep = 0;
        this.showStep();
    }

    showStep() {
        // Remove existing overlay and tooltip
        this.cleanup();

        const step = this.steps[this.currentStep];

        // Create overlay
        const overlay = document.createElement('div');
        overlay.id = 'tour-overlay';
        overlay.className = 'tour-overlay';
        document.body.appendChild(overlay);

        // Create tooltip
        const tooltip = document.createElement('div');
        tooltip.id = 'tour-tooltip';
        tooltip.className = 'tour-tooltip';

        // Add content
        tooltip.innerHTML = `
            <div class="tour-header">
                <h5 class="tour-title">${step.title}</h5>
                <button class="tour-close" onclick="onboardingTour.skip()">
                    <i class="bi bi-x-lg"></i>
                </button>
            </div>
            <div class="tour-body">
                <p>${step.content}</p>
            </div>
            <div class="tour-footer">
                <div class="tour-progress">
                    ${this.currentStep + 1} of ${this.steps.length}
                </div>
                <div class="tour-buttons">
                    ${this.currentStep > 0 ? '<button class="btn btn-sm btn-outline-secondary tour-btn-prev" onclick="onboardingTour.prev()">Back</button>' : ''}
                    ${this.currentStep < this.steps.length - 1
                        ? '<button class="btn btn-sm btn-primary tour-btn-next" onclick="onboardingTour.next()">Next</button>'
                        : '<button class="btn btn-sm btn-success tour-btn-finish" onclick="onboardingTour.finish()">Get Started!</button>'
                    }
                </div>
            </div>
        `;

        document.body.appendChild(tooltip);

        // Position tooltip and highlight element
        if (step.element) {
            const element = document.querySelector(step.element);
            if (element) {
                this.highlightElement(element, step.highlightBottom);
                this.positionTooltip(tooltip, element, step.position);
            } else {
                // Fallback to center if element not found
                this.centerTooltip(tooltip);
            }
        } else {
            // Center the tooltip
            this.centerTooltip(tooltip);
        }

        // Add fade-in animation
        setTimeout(() => {
            tooltip.classList.add('tour-visible');
        }, 10);
    }

    highlightElement(element, isBottomNav = false) {
        const rect = element.getBoundingClientRect();

        // Create spotlight
        const spotlight = document.createElement('div');
        spotlight.id = 'tour-spotlight';
        spotlight.className = 'tour-spotlight';

        // Account for scroll
        const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
        const scrollLeft = window.pageXOffset || document.documentElement.scrollLeft;

        spotlight.style.top = (rect.top + scrollTop - 10) + 'px';
        spotlight.style.left = (rect.left + scrollLeft - 10) + 'px';
        spotlight.style.width = (rect.width + 20) + 'px';
        spotlight.style.height = (rect.height + 20) + 'px';

        // For bottom nav, increase z-index to show above nav
        if (isBottomNav) {
            spotlight.style.zIndex = '10002';
        }

        document.body.appendChild(spotlight);

        // Scroll element into view
        element.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }

    positionTooltip(tooltip, element, position) {
        const rect = element.getBoundingClientRect();
        const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
        const scrollLeft = window.pageXOffset || document.documentElement.scrollLeft;

        const tooltipRect = tooltip.getBoundingClientRect();

        let top, left;

        switch(position) {
            case 'top':
                top = rect.top + scrollTop - tooltipRect.height - 20;
                left = rect.left + scrollLeft + (rect.width / 2) - (tooltipRect.width / 2);
                break;
            case 'bottom':
                top = rect.bottom + scrollTop + 20;
                left = rect.left + scrollLeft + (rect.width / 2) - (tooltipRect.width / 2);
                break;
            case 'left':
                top = rect.top + scrollTop + (rect.height / 2) - (tooltipRect.height / 2);
                left = rect.left + scrollLeft - tooltipRect.width - 20;
                break;
            case 'right':
                top = rect.top + scrollTop + (rect.height / 2) - (tooltipRect.height / 2);
                left = rect.right + scrollLeft + 20;
                break;
            default: // center
                this.centerTooltip(tooltip);
                return;
        }

        // Keep tooltip on screen
        const margin = 20;
        if (left < margin) left = margin;
        if (left + tooltipRect.width > window.innerWidth - margin) {
            left = window.innerWidth - tooltipRect.width - margin;
        }
        if (top < margin) top = margin;

        tooltip.style.top = top + 'px';
        tooltip.style.left = left + 'px';
    }

    centerTooltip(tooltip) {
        tooltip.style.top = '50%';
        tooltip.style.left = '50%';
        tooltip.style.transform = 'translate(-50%, -50%)';
    }

    next() {
        if (this.currentStep < this.steps.length - 1) {
            this.currentStep++;
            this.showStep();
        }
    }

    prev() {
        if (this.currentStep > 0) {
            this.currentStep--;
            this.showStep();
        }
    }

    skip() {
        if (confirm('Are you sure you want to skip the tour? You can restart it from Settings.')) {
            this.finish();
        }
    }

    finish() {
        localStorage.setItem('onboardingComplete', 'true');
        this.cleanup();
    }

    cleanup() {
        const overlay = document.getElementById('tour-overlay');
        const tooltip = document.getElementById('tour-tooltip');
        const spotlight = document.getElementById('tour-spotlight');

        if (overlay) overlay.remove();
        if (tooltip) tooltip.remove();
        if (spotlight) spotlight.remove();
    }

    // Allow users to restart the tour
    restart() {
        localStorage.removeItem('onboardingComplete');
        this.start(true);
    }
}

// Global instance
const onboardingTour = new OnboardingTour();

// Auto-start on page load ONLY for new users
document.addEventListener('DOMContentLoaded', function() {
    // Check if this is a new user (URL parameter from registration)
    const urlParams = new URLSearchParams(window.location.search);
    const isNewUser = urlParams.get('new_user') === 'true';

    // Only start tour for new users who just registered
    if (isNewUser) {
        // Remove the query parameter from URL without reloading
        const url = new URL(window.location);
        url.searchParams.delete('new_user');
        window.history.replaceState({}, '', url);

        // Delay tour start slightly to ensure page is fully loaded
        setTimeout(() => {
            onboardingTour.start();
        }, 500);
    }
});
