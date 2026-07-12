const tasksTableBody = document.getElementById('tasksTableBody');
const optimizeBtn = document.getElementById('optimizeBtn');
const sampleDataBtn = document.getElementById('sampleDataBtn');
const importJsonBtn = document.getElementById('importJsonBtn');
const currentMakespan = document.getElementById('currentMakespan');
const totalTasks = document.getElementById('totalTasks');
const machinesCount = document.getElementById('machinesCount');
const makespanValue = document.getElementById('makespanValue');
const utilizationValue = document.getElementById('utilizationValue');
const ganttContainer = document.getElementById('gantt');
const utilizationChartCanvas = document.getElementById('utilizationChart');

let tasks = [];
let schedule = [];
let utilizationChart;
let ganttChart;

function toDuration(task) {
  return task.duration ?? task.quantity * task.time_per_item;
}

function renderTasks() {
  tasksTableBody.innerHTML = '';

  tasks.forEach((task, index) => {
    const row = document.createElement('tr');
    row.innerHTML = `
      <td>${task.id}</td>
      <td>${task.name}</td>
      <td><input type="number" class="form-control form-control-sm quantity-input" value="${task.quantity}" data-index="${index}" min="1" /></td>
      <td><input type="text" class="form-control form-control-sm dependency-input" value="${(task.dependencies||[]).join(',')}" data-index="${index}" /></td>
      <td>${(task.possible_machines && task.possible_machines.length) ? task.possible_machines.join(', ') : (task.machine||'')}</td>
      <td>${toDuration(task)}</td>
      <td>${task.priority}</td>
    `;
    tasksTableBody.appendChild(row);
  });

  totalTasks.textContent = tasks.length;
  machinesCount.textContent = new Set(tasks.map((task) => task.machine)).size;

  document.querySelectorAll('.quantity-input').forEach((input) => {
    input.addEventListener('change', (event) => {
      const index = Number(event.target.dataset.index);
      const value = Number(event.target.value);
      tasks[index].quantity = Number.isFinite(value) && value > 0 ? value : 1;
      tasks[index].duration = tasks[index].quantity * tasks[index].time_per_item;
      renderTasks();
    });
  });

  document.querySelectorAll('.dependency-input').forEach((input) => {
    input.addEventListener('change', (event) => {
      const index = Number(event.target.dataset.index);
      const raw = event.target.value || '';
      const deps = raw
        .split(',')
        .map((s) => s.trim())
        .filter((s) => s.length > 0);
      tasks[index].dependencies = deps;
      // Keep UI in sync
      renderTasks();
    });
  });
}

function renderKpis(result) {
  const machineNames = [...new Set(result.tasks.map((task) => task.machine))];
  const totalDuration = result.tasks.reduce((sum, task) => sum + task.duration, 0);
  const averageUtilization = machineNames.length > 0 ? Math.round((totalDuration / (result.makespan * machineNames.length)) * 100) : 0;

  currentMakespan.textContent = `${result.makespan} units`;
  makespanValue.textContent = `${result.makespan}`;
  utilizationValue.textContent = `${averageUtilization}%`;
}

function renderGantt(result) {
  const scheduleItems = result.optimized_schedule || [];

  if (!scheduleItems.length) {
    ganttContainer.innerHTML = '<div class="text-muted py-4">Run optimization to populate the Gantt chart.</div>';
    return;
  }

  const machines = [...new Set(scheduleItems.map((s) => s.machine))];
  const makespan = result.makespan || Math.max(...scheduleItems.map((s) => s.finish_time), 0);

  ganttContainer.innerHTML = '';
  const legend = document.createElement('div');
  legend.className = 'gantt-legend mb-2';
  legend.textContent = `Makespan: ${makespan} units`;
  ganttContainer.appendChild(legend);

  const lanes = document.createElement('div');
  lanes.className = 'gantt-lanes';

  machines.forEach((machine) => {
    const lane = document.createElement('div');
    lane.className = 'gantt-lane';

    const label = document.createElement('div');
    label.className = 'gantt-lane-label';
    label.textContent = machine;

    const timeline = document.createElement('div');
    timeline.className = 'gantt-timeline';

    const tasksForMachine = scheduleItems.filter((s) => s.machine === machine);
    tasksForMachine.forEach((t) => {
      const bar = document.createElement('div');
      bar.className = 'gantt-task';
      const start = Number(t.start_time);
      const end = Number(t.finish_time);
      const widthPct = Math.max(2, ((end - start) / Math.max(1, makespan)) * 100);
      const leftPct = (start / Math.max(1, makespan)) * 100;
      bar.style.left = `${leftPct}%`;
      bar.style.width = `${widthPct}%`;
      bar.title = `${t.name} — ${start} → ${end} (dur ${end - start})`;
      bar.textContent = t.name;
      timeline.appendChild(bar);
    });

    lane.appendChild(label);
    lane.appendChild(timeline);
    lanes.appendChild(lane);
  });

  ganttContainer.appendChild(lanes);
}

function formatDate(value) {
  const date = new Date();
  date.setDate(date.getDate() + value);
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
}

function renderUtilizationChart(result) {
  if (utilizationChart) {
    utilizationChart.destroy();
  }

  const machineNames = [...new Set(result.tasks.map((task) => task.machine))];
  const usage = machineNames.map((machine) => {
    const machineDuration = result.tasks
      .filter((task) => task.machine === machine)
      .reduce((sum, task) => sum + task.duration, 0);
    return Math.round((machineDuration / result.makespan) * 100);
  });

  utilizationChart = new Chart(utilizationChartCanvas, {
    type: 'bar',
    data: {
      labels: machineNames,
      datasets: [
        {
          label: 'Utilization %',
          data: usage,
          backgroundColor: ['#3b82f6', '#60a5fa', '#2563eb'],
        },
      ],
    },
    options: {
      responsive: true,
      plugins: {
        legend: { display: false },
      },
      scales: {
        y: { beginAtZero: true, max: 100 },
      },
    },
  });
}

async function fetchTasks() {
  const response = await fetch('http://127.0.0.1:8000/tasks');
  tasks = await response.json();
  renderTasks();
}

async function optimizeTasks() {
  const response = await fetch('http://127.0.0.1:8000/optimize', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ tasks }),
  });

  const data = await response.json();
  schedule = data.optimized_schedule || [];
  renderKpis(data);
  renderGantt(data);
  renderUtilizationChart(data);
}

async function loadSampleData() {
  const response = await fetch('./sample-data.json');
  tasks = await response.json();
  tasks = tasks.map((task) => ({
    ...task,
    duration: task.duration ?? task.quantity * task.time_per_item,
  }));
  renderTasks();
}

function importJson() {
  const input = document.createElement('input');
  input.type = 'file';
  input.accept = 'application/json';
  input.onchange = async (event) => {
    const file = event.target.files[0];
    if (!file) return;
    const text = await file.text();
    tasks = JSON.parse(text);
    tasks = tasks.map((task) => ({
      ...task,
      duration: task.duration ?? task.quantity * task.time_per_item,
    }));
    renderTasks();
  };
  input.click();
}

optimizeBtn.addEventListener('click', optimizeTasks);
sampleDataBtn.addEventListener('click', loadSampleData);
importJsonBtn.addEventListener('click', importJson);

fetchTasks();
loadSampleData();
