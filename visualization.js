document.addEventListener('DOMContentLoaded', function() {
    fetch('user_metrics.json')
        .then(response => response.json())
        .then(data => {
            // Define the order of days
            const daysOfWeekOrder = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
            
            // Order the data according to the days of the week
            const orderedWinRateData = daysOfWeekOrder.map(day => data.win_rate_by_day[day] || 0);

            // Data for the white pie chart
            const whitePieData = {
                labels: ['Win', 'Loss', 'Draw'],
                datasets: [{
                    data: [
                        data.outcome_by_colour.white.win,
                        data.outcome_by_colour.white.loss,
                        data.outcome_by_colour.white.draw
                    ],
                    backgroundColor: ['#36a2eb', '#ff6384', '#ffcd56']
                }]
            };

            // Data for the black pie chart
            const blackPieData = {
                labels: ['Win', 'Loss', 'Draw'],
                datasets: [{
                    data: [
                        data.outcome_by_colour.black.win,
                        data.outcome_by_colour.black.loss,
                        data.outcome_by_colour.black.draw
                    ],
                    backgroundColor: ['#36a2eb', '#ff6384', '#ffcd56']
                }]
            };

            // Data for the win rate bar chart
            const winRateBarData = {
                labels: daysOfWeekOrder,
                datasets: [{
                    label: 'Win Rate',
                    data: orderedWinRateData,
                    backgroundColor: '#36a2eb'
                }]
            };

            // Create the white pie chart
            const whitePieCtx = document.getElementById('whitePieChart').getContext('2d');
            const whitePieChart = new Chart(whitePieCtx, {
                type: 'pie',
                data: whitePieData,
                options: {
                    plugins: {
                        title: {
                            display: true,
                            text: 'Win/Loss/Draw Rate When White'
                        }
                    }
                }
            });

            // Create the black pie chart
            const blackPieCtx = document.getElementById('blackPieChart').getContext('2d');
            const blackPieChart = new Chart(blackPieCtx, {
                type: 'pie',
                data: blackPieData,
                options: {
                    plugins: {
                        title: {
                            display: true,
                            text: 'Win/Loss/Draw Rate When Black'
                        }
                    }
                }
            });

            // Create the win rate bar chart
            const winRateBarCtx = document.getElementById('winRateBarChart').getContext('2d');
            const winRateBarChart = new Chart(winRateBarCtx, {
                type: 'bar',
                data: winRateBarData,
                options: {
                    plugins: {
                        title: {
                            display: true,
                            text: 'Win Rate by Day of the Week'
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            max: 1
                        }
                    }
                }
            });
        })
        .catch(error => console.error('Error loading the JSON data:', error));
});
