let gameState = {
    selectedAnimal: null, xp: 0, level: 1, timerSeconds: 1500, isRunning: false,
    isPaused: false, isWorkSession: true, sessionsCompleted: 0, focusMinutesTotal: 0,
    xpGainedToday: 0, focusDuration: 25, breakDuration: 5, todos: []
};

let timerInterval = null, focusDuration = 25 * 60, breakDuration = 5 * 60;
const XP_PER_MINUTE = 10;

const animals = {
    passaro: { name: 'Pássaro', type: 'Criativo', image: '/static/passaro.gif' },
    coruja: { name: 'Coruja', type: 'Sábio', image: '/static/coruja.gif' },
    raposa: { name: 'Raposa', type: 'Estratégico', image: '/static/raposa.gif' }
};

document.addEventListener('DOMContentLoaded', () => {
    try {
        loadGameState();
        if (gameState.selectedAnimal) {
            document.getElementById('selection-phase').classList.add('hidden');
            document.getElementById('session-phase').classList.remove('hidden');
            gsap.set('#session-phase', { opacity: 1, y: 0 });
            updateAnimalInfo();
            updateDisplay();
            renderTodos();
        } else {
            gsap.from('#selection-phase', { duration: 0.6, opacity: 0, y: 20, ease: "power2.out" });
        }
    } catch (err) { console.error('Init error:', err); }

    let retries = 0;
    const tryInitThree = () => {
        if (typeof THREE !== 'undefined') {
            initThreeJS();
        } else if (retries < 5) {
            retries++;
            setTimeout(tryInitThree, 200);
        }
    };
    tryInitThree();

    try { initLenis(); } catch (err) { console.warn('Lenis not available:', err); }
});

function saveGameState() { localStorage.setItem('pomodoroGameState', JSON.stringify(gameState)); }
function loadGameState() {
    const saved = localStorage.getItem('pomodoroGameState');
    if (saved) {
        gameState = { ...gameState, ...JSON.parse(saved) };
        gameState.isRunning = gameState.isPaused = false;
    }
    focusDuration = gameState.focusDuration * 60;
    breakDuration = gameState.breakDuration * 60;
}

function selectAnimal(id) {
    gameState.selectedAnimal = id;
    gameState.xp = gameState.level = 0;
    gameState.level = 1;
    saveGameState();
    gsap.to('#selection-phase', {
        duration: 0.4, opacity: 0, y: -20, ease: "power2.in",
        onComplete: () => transitionToSession()
    });
}

function transitionToSession() {
    try {
        document.getElementById('selection-phase').classList.add('hidden');
        document.getElementById('session-phase').classList.remove('hidden');
        gsap.set('#session-phase', { opacity: 1, y: 0 });
        updateAnimalInfo();
        updateDisplay();
        renderTodos();
        gsap.from('#session-phase', { duration: 0.6, opacity: 0, y: 20, ease: "power2.out" });
    } catch (err) { console.error('Transition error:', err); }
}

function updateAnimalInfo() {
    const animal = animals[gameState.selectedAnimal];
    document.getElementById('animal-emoji').src = animal.image;
    document.getElementById('animal-emoji-large').src = animal.image;
    document.getElementById('animal-name').textContent = animal.name;
    document.getElementById('animal-type').textContent = animal.type;
}

function changeAnimal() {
    if (confirm('Trocar de animal? Perderá todo progresso!')) {
        gameState.selectedAnimal = null;
        gameState.xp = gameState.level = 0;
        gameState.level = 1;
        gameState.isRunning = gameState.isPaused = false;
        saveGameState();
        gsap.to('#session-phase', {
            duration: 0.4, opacity: 0, y: -20, ease: "power2.in",
            onComplete: () => {
                document.getElementById('session-phase').classList.add('hidden');
                document.getElementById('selection-phase').classList.remove('hidden');
                gsap.from('#selection-phase', { duration: 0.6, opacity: 0, y: 20, ease: "power2.out" });
            }
        });
    }
}

function startTimer() {
    gameState.isRunning = true;
    gameState.isPaused = false;
    updateButtons();
    timerInterval = setInterval(() => {
        if (gameState.timerSeconds > 0) {
            gameState.timerSeconds--;
            if (gameState.isWorkSession && gameState.timerSeconds % 60 === 0 && gameState.timerSeconds > 0) {
                addXP(XP_PER_MINUTE);
            }
            updateDisplay();
        } else {
            completeTimer();
        }
    }, 1000);
}

function pauseTimer() {
    gameState.isRunning = false;
    gameState.isPaused = true;
    clearInterval(timerInterval);
    updateButtons();
}

function resumeTimer() {
    gameState.isRunning = true;
    gameState.isPaused = false;
    startTimer();
}

function resetTimer() {
    gameState.isRunning = gameState.isPaused = false;
    clearInterval(timerInterval);
    gameState.timerSeconds = gameState.isWorkSession ? focusDuration : breakDuration;
    updateButtons();
    updateDisplay();
}

function completeTimer() {
    clearInterval(timerInterval);
    gameState.isRunning = gameState.isPaused = false;
    if (gameState.isWorkSession) {
        gameState.sessionsCompleted++;
        gameState.focusMinutesTotal += gameState.focusDuration;
        addXP(XP_PER_MINUTE);
        gameState.isWorkSession = false;
        gameState.timerSeconds = breakDuration;
        playSound();
        showNotification('Descanse! ☕');
        setTimeout(() => startTimer(), 1000);
    } else {
        gameState.isWorkSession = true;
        gameState.timerSeconds = focusDuration;
        playSound();
        showNotification('Vamos focar! 🚀');
    }
    saveGameState();
    updateButtons();
    updateDisplay();
}

function addXP(amount) {
    gameState.xp += amount;
    gameState.xpGainedToday += amount;
    if (gameState.xp >= 100) {
        gameState.xp = gameState.xp % 100;
        gameState.level++;
        gsap.to('#animal-emoji', {
            duration: 0.3, scale: 1.4, repeat: 1, yoyo: true, ease: "back.out"
        });
        showNotification(`⭐ Nível ${gameState.level}!`);
    }
    saveGameState();
    updateDisplay();
}

function updateDisplay() {
    const min = Math.floor(gameState.timerSeconds / 60);
    const sec = gameState.timerSeconds % 60;
    document.getElementById('timer-min').textContent = min.toString().padStart(2, '0');
    document.getElementById('timer-sec').textContent = sec.toString().padStart(2, '0');

    const status = document.getElementById('session-status');
    status.textContent = gameState.isWorkSession ? '⏱️ Foco' : '☕ Pausa';
    status.className = gameState.isWorkSession ? 'badge-focus' : 'badge-break';

    const total = gameState.isWorkSession ? focusDuration : breakDuration;
    const progress = ((total - gameState.timerSeconds) / total) * 100;
    document.getElementById('timer-fill').style.width = progress + '%';

    document.getElementById('level').textContent = gameState.level;
    document.getElementById('xp-curr').textContent = gameState.xp;
    document.getElementById('xp-fill').style.width = (gameState.xp / 100) * 100 + '%';

    document.getElementById('stat-min').textContent = gameState.focusMinutesTotal;
    document.getElementById('stat-xp').textContent = gameState.xpGainedToday;
    document.getElementById('stat-sessions').textContent = gameState.sessionsCompleted;
}

function updateButtons() {
    const [startBtn, pauseBtn, resumeBtn] = ['start-btn', 'pause-btn', 'resume-btn'].map(id => document.getElementById(id));
    startBtn.classList.add('hidden');
    pauseBtn.classList.add('hidden');
    resumeBtn.classList.add('hidden');
    if (gameState.isRunning) pauseBtn.classList.remove('hidden');
    else if (gameState.isPaused) resumeBtn.classList.remove('hidden');
    else startBtn.classList.remove('hidden');
}

function addTodo() {
    const input = document.getElementById('todo-input');
    const text = input.value.trim();
    if (!text) return;
    gameState.todos.push({ id: Date.now(), text, completed: false });
    input.value = '';
    saveTodos();
    renderTodos();
}

function toggleTodo(id) {
    gameState.todos.find(t => t.id === id).completed = !gameState.todos.find(t => t.id === id).completed;
    saveTodos();
    renderTodos();
}

function deleteTodo(id) {
    gameState.todos = gameState.todos.filter(t => t.id !== id);
    saveTodos();
    renderTodos();
}

function renderTodos() {
    const list = document.getElementById('todo-list');
    if (!gameState.todos.length) {
        list.innerHTML = '<p class="text-xs text-gray-500 text-center py-4">Nenhuma tarefa</p>';
        return;
    }
    list.innerHTML = gameState.todos.map(t => `
        <div class="todo-item ${t.completed ? 'completed' : ''}">
            <input type="checkbox" ${t.completed ? 'checked' : ''} onchange="toggleTodo(${t.id})" class="w-4 h-4">
            <span class="flex-1 text-sm">${t.text}</span>
            <button onclick="deleteTodo(${t.id})" class="text-xs text-red-600 hover:text-red-800">✕</button>
        </div>
    `).join('');
}

function clearCompleted() {
    gameState.todos = gameState.todos.filter(t => !t.completed);
    saveTodos();
    renderTodos();
}

function saveTodos() {
    const state = JSON.parse(localStorage.getItem('pomodoroGameState') || '{}');
    state.todos = gameState.todos;
    localStorage.setItem('pomodoroGameState', JSON.stringify(state));
}

function toggleSettings() {
    const panel = document.getElementById('settings-panel');
    gsap.to(panel, {
        duration: 0.3, opacity: panel.classList.contains('hidden') ? 1 : 0, ease: "power2.inOut",
        onComplete: () => panel.classList.toggle('hidden')
    });
}

function applySettings() {
    gameState.focusDuration = Math.max(1, Math.min(60, parseInt(document.getElementById('focus-input').value) || 25));
    gameState.breakDuration = Math.max(1, Math.min(30, parseInt(document.getElementById('break-input').value) || 5));
    focusDuration = gameState.focusDuration * 60;
    breakDuration = gameState.breakDuration * 60;
    if (!gameState.isRunning && !gameState.isPaused) {
        gameState.timerSeconds = focusDuration;
        updateDisplay();
    }
    saveGameState();
    showNotification('✅ Atualizado!');
    setTimeout(() => toggleSettings(), 300);
}

function playSound() {
    try { document.getElementById('notification-sound').play(); } catch (e) {}
}

function showNotification(msg) {
    const notif = document.createElement('div');
    notif.className = 'fixed top-6 right-6 bg-black text-white px-6 py-3 rounded-lg font-semibold';
    notif.textContent = msg;
    document.body.appendChild(notif);
    gsap.from(notif, { duration: 0.3, opacity: 0, y: -20, ease: "back.out" });
    gsap.to(notif, { duration: 0.3, opacity: 0, y: -20, ease: "back.in", delay: 2.7 });
    setTimeout(() => notif.remove(), 3000);
}

document.getElementById('todo-input')?.addEventListener('keypress', e => { if (e.key === 'Enter') addTodo(); });
setInterval(() => saveGameState(), 5000);

function initThreeJS() {
    try {
        if (typeof THREE === 'undefined' || !document.getElementById('three-canvas')) return;
        const canvas = document.getElementById('three-canvas');
        const scene = new THREE.Scene();
        scene.background = null;
        const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
        camera.position.set(0, 10, 20);
        const renderer = new THREE.WebGLRenderer({ canvas, alpha: true, antialias: true });
        renderer.setSize(window.innerWidth, window.innerHeight);
        renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
        const light = new THREE.DirectionalLight(0xffffff, 0.4);
        light.position.set(10, 20, 10);
        scene.add(light);
        scene.add(new THREE.AmbientLight(0xffffff, 0.3));
        const objects = [];
        for (let i = 0; i < 6; i++) {
            const geometry = Math.random() > 0.5 ? new THREE.BoxGeometry(1, 1, 1) : new THREE.SphereGeometry(0.7, 32, 32);
            const material = new THREE.MeshStandardMaterial({
                color: i % 2 === 0 ? 0xf0f0f0 : 0xe0e0e0, roughness: 0.7, metalness: 0.1
            });
            const mesh = new THREE.Mesh(geometry, material);
            mesh.position.set((Math.random() - 0.5) * 30, 5 + Math.random() * 15, (Math.random() - 0.5) * 30);
            scene.add(mesh);
            objects.push(mesh);
        }
        window.addEventListener('resize', () => {
            camera.aspect = window.innerWidth / window.innerHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(window.innerWidth, window.innerHeight);
        });
        function animate() {
            requestAnimationFrame(animate);
            objects.forEach((obj, i) => {
                obj.rotation.x += 0.002;
                obj.rotation.y += 0.003;
                obj.position.y += Math.sin(Date.now() * 0.001 + i) * 0.005;
            });
            renderer.render(scene, camera);
        }
        animate();
    } catch (err) { console.error('Three.js error:', err); }
}

function initLenis() {
    try {
        if (typeof Lenis === 'undefined') return;
        const lenis = new Lenis({ lerp: 0.1, wheelMultiplier: 1 });
        function raf(time) {
            lenis.raf(time);
            requestAnimationFrame(raf);
        }
        requestAnimationFrame(raf);
    } catch (err) { console.warn('Lenis error:', err); }
}
