/**
 * Dashboard JavaScript for FlyPig LINE Bot Admin
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize activity chart
    initActivityChart();
});

/**
 * Initialize the bot activity chart
 */
function initActivityChart() {
    const ctx = document.getElementById('activityChart');
    
    if (!ctx) return;
    
    // Generate sample data for the past 7 days
    const labels = [];
    const userMessages = [];
    const botMessages = [];
    
    // Get dates for the last 7 days
    for (let i = 6; i >= 0; i--) {
        const date = new Date();
        date.setDate(date.getDate() - i);
        labels.push(date.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' }));
        
        // Random data for demonstration
        userMessages.push(Math.floor(Math.random() * 20 + 5));
        botMessages.push(Math.floor(Math.random() * 20 + 5));
    }
    
    // Create chart
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'User Messages',
                    data: userMessages,
                    borderColor: 'rgba(13, 110, 253, 1)',
                    backgroundColor: 'rgba(13, 110, 253, 0.1)',
                    tension: 0.4,
                    fill: true
                },
                {
                    label: 'Bot Responses',
                    data: botMessages,
                    borderColor: 'rgba(25, 135, 84, 1)',
                    backgroundColor: 'rgba(25, 135, 84, 0.1)',
                    tension: 0.4,
                    fill: true
                }
            ]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'top',
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Message Count'
                    },
                    ticks: {
                        precision: 0
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Date'
                    }
                }
            },
            interaction: {
                intersect: false,
                mode: 'index',
            }
        }
    });
}

/**
 * Updates dashboard stats with real-time data
 * This function would be used if we implemented websockets for real-time updates
 */
function updateDashboardStats(stats) {
    // Update user count
    const userCountElement = document.querySelector('.card-title:contains("LINE Users") + .card-text');
    if (userCountElement && stats.userCount) {
        userCountElement.textContent = stats.userCount;
    }
    
    // Update message count
    const messageCountElement = document.querySelector('.card-title:contains("Messages") + .card-text');
    if (messageCountElement && stats.messageCount) {
        messageCountElement.textContent = stats.messageCount;
    }
    
    // Update document count
    const docCountElement = document.querySelector('.card-title:contains("Documents") + .card-text');
    if (docCountElement && stats.documentCount) {
        docCountElement.textContent = stats.documentCount;
    }
}

/**
 * Refresh recent messages in the dashboard
 * This would be connected to a server-sent event or websocket in a production environment
 */
function refreshRecentMessages() {
    // In a real implementation, this would fetch new messages from the server
    // For now, we'll just reload the page
    location.reload();
}
