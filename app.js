const state = JSON.parse(localStorage.getItem('wordvoyage-state') || 'null') || { newGoal: 20, reviewGoal: 30, newDone: 12, reviewDone: 18, streak: 7 };
const viewNames = { overview: '今日航程', study: '开始学习', map: '词汇地图', mistakes: '错词修炼场', stats: '学习统计', settings: '学习设置' };
const $ = (s) => document.querySelector(s);
const $$ = (s) => [...document.querySelectorAll(s)];

function save() { localStorage.setItem('wordvoyage-state', JSON.stringify(state)); }
function showToast(text) { const toast = $('#toast'); toast.textContent = text; toast.classList.add('show'); setTimeout(() => toast.classList.remove('show'), 1800); }
function updateGoals() {
  $('#newGoal').textContent = state.newGoal; $('#reviewGoal').textContent = state.reviewGoal;
  $('#newWordsInput').value = state.newGoal; $('#reviewLimitInput').value = state.reviewGoal;
  $('#previewTotal').textContent = state.newGoal + state.reviewGoal; $('#previewNew').textContent = state.newGoal; $('#previewReview').textContent = state.reviewGoal;
  $('#previewTime').textContent = Math.max(10, Math.round((state.newGoal + state.reviewGoal) * .5));
  $('#newDone').textContent = Math.min(state.newDone, state.newGoal); $('#reviewDone').textContent = Math.min(state.reviewDone, state.reviewGoal);
  const newPct = Math.round(Math.min(100, state.newDone / state.newGoal * 100)); const reviewPct = Math.round(Math.min(100, state.reviewDone / state.reviewGoal * 100));
  $('#newRing').style.background = `conic-gradient(currentColor 0 ${newPct}%,#edf0f4 ${newPct}% 100%)`; $('#newRing span').textContent = newPct + '%';
  $('#reviewRing').style.background = `conic-gradient(currentColor 0 ${reviewPct}%,#edf0f4 ${reviewPct}% 100%)`; $('#reviewRing span').textContent = reviewPct + '%';
}
function switchView(view) {
  $$('.view').forEach((el) => el.classList.toggle('active-view', el.id === `view-${view}`));
  $$('.nav-item[data-view]').forEach((el) => el.classList.toggle('active', el.dataset.view === view));
  $('#pageCrumb').textContent = viewNames[view] || viewNames.overview; $('#sidebar').classList.remove('open'); window.scrollTo({ top: 0, behavior: 'smooth' });
}
$$('[data-view]').forEach((el) => el.addEventListener('click', () => switchView(el.dataset.view)));
$('#menuButton').addEventListener('click', () => $('#sidebar').classList.toggle('open'));
$$('.stepper button').forEach((button) => button.addEventListener('click', () => {
  const type = button.dataset.step; const key = type === 'new' ? 'newGoal' : 'reviewGoal'; const input = button.parentElement.querySelector('input');
  state[key] = Math.max(Number(input.min), Math.min(Number(input.max), state[key] + Number(button.dataset.change))); save(); updateGoals(); showToast('学习目标已保存');
}));
$$('.stepper input').forEach((input) => input.addEventListener('change', () => { const key = input.id === 'newWordsInput' ? 'newGoal' : 'reviewGoal'; state[key] = Math.max(Number(input.min), Math.min(Number(input.max), Number(input.value) || Number(input.min))); save(); updateGoals(); showToast('学习目标已保存'); }));
$$('.answer-button').forEach((button) => button.addEventListener('click', () => {
  const answer = button.dataset.answer; if (answer === 'again') { state.newDone = Math.max(0, state.newDone - 1); showToast('已加入强化队列，1 分钟后再见'); } else { state.newDone = Math.min(state.newGoal, state.newDone + 1); showToast(answer === 'easy' ? '+20 XP，记得很牢' : '+10 XP，稍后再复习'); }
  save(); updateGoals(); const index = Number($('#studyIndex').textContent); $('#studyIndex').textContent = Math.min(8, index + 1); $('#studyProgress').style.width = `${Math.min(100, (index + 1) / 8 * 100)}%`;
}));
$('#soundButton').addEventListener('click', () => { if ('speechSynthesis' in window) { speechSynthesis.cancel(); speechSynthesis.speak(new SpeechSynthesisUtterance($('#wordText').textContent)); showToast('正在播放发音'); } else showToast('当前浏览器不支持发音'); });
$$('.segmented button').forEach((button) => button.addEventListener('click', () => { $$('.segmented button').forEach((b) => b.classList.remove('selected')); button.classList.add('selected'); showToast('发音偏好已更新'); }));
updateGoals();
