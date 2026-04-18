(function() {
  const micBtn = document.getElementById('mic-btn');
  const micStatus = document.getElementById('mic-status');
  const textarea = document.getElementById('answer');
  const feedbackEl = document.getElementById('live-feedback');
  const feedbackText = document.getElementById('feedback-text');

  if (!micBtn || !textarea) return;

  // --- Speech-to-Text ---
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) {
    micBtn.style.display = 'none';
    return;
  }

  const recognition = new SpeechRecognition();
  recognition.continuous = true;
  recognition.interimResults = true;
  recognition.lang = 'en-US';
  let isListening = false;
  let finalTranscript = textarea.value;

  micBtn.addEventListener('click', function() {
    if (isListening) {
      recognition.stop();
    } else {
      finalTranscript = textarea.value;
      recognition.start();
    }
  });

  recognition.onstart = function() {
    isListening = true;
    micBtn.style.background = 'rgba(163,64,64,0.12)';
    micBtn.style.borderColor = 'var(--danger)';
    micStatus.textContent = 'Listening…';
  };

  recognition.onend = function() {
    isListening = false;
    micBtn.style.background = 'none';
    micBtn.style.borderColor = 'var(--border2)';
    micStatus.textContent = '';
  };

  recognition.onresult = function(event) {
    let interim = '';
    for (let i = event.resultIndex; i < event.results.length; i++) {
      const t = event.results[i][0].transcript;
      if (event.results[i].isFinal) {
        finalTranscript += (finalTranscript ? ' ' : '') + t;
      } else {
        interim += t;
      }
    }
    textarea.value = finalTranscript + (interim ? ' ' + interim : '');
  };

  recognition.onerror = function(e) {
    micStatus.textContent = e.error === 'not-allowed' ? 'Mic access denied' : '';
    isListening = false;
    micBtn.style.background = 'none';
    micBtn.style.borderColor = 'var(--border2)';
  };

  // --- Live AI Evaluation (on blur) ---
  const evaluateUrl = document.getElementById('evaluate-url');
  const csrfToken = document.getElementById('csrf-token');
  const questionText = document.getElementById('question-text');

  if (!evaluateUrl || !csrfToken || !feedbackEl || !feedbackText) return;

  let evalTimeout;
  textarea.addEventListener('blur', function() {
    clearTimeout(evalTimeout);
    const answer = textarea.value.trim();
    if (answer.length < 20) return;

    evalTimeout = setTimeout(function() {
      feedbackEl.style.display = 'block';
      feedbackText.textContent = 'Evaluating…';

      fetch(evaluateUrl.value, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrfToken.value,
        },
        body: JSON.stringify({
          question: questionText.value,
          answer: answer,
        }),
      })
      .then(r => r.json())
      .then(data => {
        if (data.error) {
          feedbackEl.style.display = 'none';
        } else {
          const scoreStr = data.score ? ' · Score: ' + data.score + '/10' : '';
          feedbackText.innerHTML =
            '<strong style="color:var(--success);">' + scoreStr + '</strong> ' +
            (data.feedback || '');
        }
      })
      .catch(() => { feedbackEl.style.display = 'none'; });
    }, 500);
  });
})();
