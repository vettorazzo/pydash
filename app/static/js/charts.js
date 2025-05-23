let cpuChart, memoryChart, networkChart, storageChart;

function updateCharts(data) {
    // Update CPU Chart
    updateCpuChart(data);
    
    // Update Memory Chart
    updateMemoryChart(data);
    
    // Update Network Chart
    updateNetworkChart(data);
    
    // Update Storage Chart
    updateStorageChart(data);
    
    // Update system info
    updateSystemInfo();
    
    // Update timestamps
    document.querySelectorAll('.update-time').forEach(el => {
        el.textContent = new Date().toLocaleTimeString();
    });
}

function updateCpuChart(data) {
    const ctx = document.getElementById('cpuChart').getContext('2d');
    const cpuData = data['cpu_util'] || { data: [] };
    
    const labels = cpuData.data.map(item => new Date(item.timestamp * 1000).toLocaleTimeString());
    const values = cpuData.data.map(item => parseFloat(item.value));
    
    if (cpuChart) {
        cpuChart.data.labels = labels;
        cpuChart.data.datasets[0].data = values;
        cpuChart.update();
    } else {
        cpuChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'CPU Usage %',
                    data: values,
                    backgroundColor: 'rgba(54, 162, 235, 0.2)',
                    borderColor: 'rgba(54, 162, 235, 1)',
                    borderWidth: 2,
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100,
                        ticks: {
                            callback: function(value) {
                                return value + '%';
                            }
                        }
                    }
                }
            }
        });
    }
}

function updateMemoryChart(data) {
    const ctx = document.getElementById('memoryChart').getContext('2d');
    const total = data['memory_total'] || { data: [] };
    const used = data['memory_used'] || { data: [] };
    const free = data['memory_free'] || { data: [] };
    
    const labels = total.data.map(item => new Date(item.timestamp * 1000).toLocaleTimeString());
    const totalValues = total.data.map(item => parseFloat(item.value) / (1024 * 1024));
    const usedValues = used.data.map(item => parseFloat(item.value) / (1024 * 1024));
    const freeValues = free.data.map(item => parseFloat(item.value) / (1024 * 1024));
    
    if (memoryChart) {
        memoryChart.data.labels = labels;
        memoryChart.data.datasets[0].data = usedValues;
        memoryChart.data.datasets[1].data = freeValues;
        memoryChart.update();
    } else {
        memoryChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Used (GB)',
                        data: usedValues,
                        backgroundColor: 'rgba(255, 99, 132, 0.7)',
                        borderColor: 'rgba(255, 99, 132, 1)',
                        borderWidth: 1
                    },
                    {
                        label: 'Free (GB)',
                        data: freeValues,
                        backgroundColor: 'rgba(75, 192, 192, 0.7)',
                        borderColor: 'rgba(75, 192, 192, 1)',
                        borderWidth: 1
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: {
                        stacked: true,
                    },
                    y: {
                        stacked: true,
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return value + ' GB';
                            }
                        }
                    }
                }
            }
        });
    }
}

function updateNetworkChart(data) {
    const ctx = document.getElementById('networkChart').getContext('2d');
    const inTraffic = data['network_in'] || { data: [] };
    const outTraffic = data['network_out'] || { data: [] };
    
    const labels = inTraffic.data.map(item => new Date(item.timestamp * 1000).toLocaleTimeString());
    const inValues = inTraffic.data.map(item => parseFloat(item.value) / (1024 * 1024));
    const outValues = outTraffic.data.map(item => parseFloat(item.value) / (1024 * 1024));
    
    if (networkChart) {
        networkChart.data.labels = labels;
        networkChart.data.datasets[0].data = inValues;
        networkChart.data.datasets[1].data = outValues;
        networkChart.update();
    } else {
        networkChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'In (MB/s)',
                        data: inValues,
                        backgroundColor: 'rgba(54, 162, 235, 0.2)',
                        borderColor: 'rgba(54, 162, 235, 1)',
                        borderWidth: 2,
                        tension: 0.4
                    },
                    {
                        label: 'Out (MB/s)',
                        data: outValues,
                        backgroundColor: 'rgba(255, 159, 64, 0.2)',
                        borderColor: 'rgba(255, 159, 64, 1)',
                        borderWidth: 2,
                        tension: 0.4
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return value + ' MB/s';
                            }
                        }
                    }
                }
            }
        });
    }
}

function updateStorageChart(data) {
    const ctx = document.getElementById('storageChart').getContext('2d');
    const total = data['disk_total'] || { data: [] };
    const used = data['disk_used'] || { data: [] };
    const free = data['disk_free'] || { data: [] };
    
    const labels = total.data.map(item => new Date(item.timestamp * 1000).toLocaleTimeString());
    const totalValues = total.data.map(item => parseFloat(item.value) / (1024 * 1024 * 1024));
    const usedValues = used.data.map(item => parseFloat(item.value) / (1024 * 1024 * 1024));
    const freeValues = free.data.map(item => parseFloat(item.value) / (1024 * 1024 * 1024));
    
    if (storageChart) {
        storageChart.data.labels = labels;
        storageChart.data.datasets[0].data = usedValues;
        storageChart.data.datasets[1].data = freeValues;
        storageChart.update();
    } else {
        storageChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Used (GB)',
                        data: usedValues,
                        backgroundColor: 'rgba(255, 99, 132, 0.2)',
                        borderColor: 'rgba(255, 99, 132, 1)',
                        borderWidth: 2,
                        tension: 0.4,
                        fill: true
                    },
                    {
                        label: 'Free (GB)',
                        data: freeValues,
                        backgroundColor: 'rgba(75, 192, 192, 0.2)',
                        borderColor: 'rgba(75, 192, 192, 1)',
                        borderWidth: 2,
                        tension: 0.4,
                        fill: true
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return value + ' GB';
                            }
                        }
                    }
                }
            }
        });
    }
}

function updateSystemInfo() {
    // In a real implementation, you would update this with actual host data
    document.getElementById('host-name').textContent = 'Home Lab Server';
    document.getElementById('host-ip').textContent = '192.168.1.100';
    document.getElementById('host-status').textContent = 'Online';
    document.getElementById('cpu-cores').textContent = '8 cores';
    document.getElementById('total-memory').textContent = '32GB';
    document.getElementById('last-check').textContent = new Date().toLocaleTimeString();
}