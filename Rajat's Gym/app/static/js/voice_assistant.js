/**
 * SmartGym Voice Assistant
 * ─────────────────────────────────────────
 * Features:
 *  • Speech-to-Text (Web Speech API)
 *  • AI response logic (keyword matching + smart replies)
 *  • Text-to-Speech (SpeechSynthesis)
 *  • English / Hindi language toggle
 *  • Real-time listening animation
 */

'use strict';

// ── State ──────────────────────────────────────────────────────────────────
let recognition  = null;
let isListening  = false;
let currentLang  = 'en';   // 'en' | 'hi'
const synth      = window.speechSynthesis;

// ── DOM Refs ───────────────────────────────────────────────────────────────
const btn        = document.getElementById('voice-btn');
const responseEl = document.getElementById('va-response');
const langBtn    = document.getElementById('lang-toggle');

// ── Response Knowledge Base ────────────────────────────────────────────────
const KB = {
    en: {
        greeting: [
            "Hey! Ready to crush today's workout?",
            "Hello! I'm your SmartGym AI coach. How can I help?",
            "Hi there! Let's make today count. What do you need?",
        ],
        workout: [
            "Check your Dashboard — today's workout plan is displayed automatically!",
            "Head to Dashboard to see today's exercises. Your plan is personalised for you.",
            "Your workout plan is on the Dashboard. Tap 'Log Today's Workout' to track it.",
        ],
        bmi: [
            "Your BMI is shown on the right panel of your Dashboard.",
            "Check the Profile card on your Dashboard for your current BMI and body stats.",
        ],
        diet: [
            "Go to Diet from the navbar for a personalised meal plan!",
            "Click Diet in the navigation. You'll find calorie targets and meal suggestions.",
        ],
        calorie: [
            "Use the Calorie Calculator in Quick Links on your Dashboard!",
            "The Calorie Calculator is under Quick Links — it calculates TDEE and macros.",
        ],
        calendar: [
            "The Workout Calendar lets you click any date to log or review workouts.",
            "Tap Calendar in the navbar to open your visual workout log.",
        ],
        progress: [
            "Check the Progress Tracker in Quick Links to see your improvement.",
            "Your streak and completed workout count are shown at the top of the Dashboard.",
        ],
        motivation: [
            "You're stronger than you think! Every rep is progress. 💪",
            "Champions are built in the moments you want to quit. Keep going!",
            "The only bad workout is the one that didn't happen. Show up!",
            "Your future self will thank you for every workout you complete today.",
            "Pain is temporary. Quitting lasts forever. Push through!",
            "You didn't come this far to only come this far. Let's go!",
        ],
        plan: [
            "Your AI-generated workout plan is shown on your Dashboard every day.",
            "Your personalised plan was created based on your goal and experience level.",
        ],
        rest: [
            "Rest days are essential! Muscles grow during recovery, not during workouts.",
            "Taking a rest day? Smart! Recovery is part of the training process. 🌿",
        ],
        strength: [
            "Go to the Strength Test page to benchmark your current fitness level.",
            "Strength Test is in Quick Links. Track your 1RM and progress over time.",
        ],
        admin: [
            "The Admin portal is at /admin/login. Only authorised trainers can access it.",
        ],
        default: [
            "I'm your SmartGym AI coach! Ask me about workouts, diet, BMI, or say 'motivate me'.",
            "Try asking: 'What's my workout today?' or 'Give me motivation' or 'Show my BMI'.",
            "I can help with workout plans, diet tips, progress tracking, and more!",
        ],
    },
    hi: {
        greeting: [
            "Namaste! Aaj ka workout shuru karne ke liye taiyar hain? 💪",
            "Hello! Main aapka SmartGym AI coach hoon. Kya poochna hai?",
            "Kya haal hain! Aaj kuch khas karna hai? Batao!",
        ],
        workout: [
            "Dashboard mein jaao — aaj ka workout plan wahan automatically dikhta hai!",
            "Aapka personalised workout plan Dashboard par hai. Abhi check karo.",
        ],
        bmi: [
            "Aapka BMI Dashboard ke right panel mein dikh raha hai.",
            "Dashboard ke Profile card mein apna BMI aur body stats dekho.",
        ],
        diet: [
            "Navbar se Diet page pe jaao — wahan personalised meal plan milega!",
            "Diet section mein calories aur macros ki jaankari milegi.",
        ],
        calorie: [
            "Dashboard ke Quick Links mein Calorie Calculator hai. Zaroor use karo!",
        ],
        calendar: [
            "Workout Calendar mein koi bhi date click karke workout log kar sakte ho.",
            "Calendar mein apni poori workout history visual tarike se dekh sakte ho.",
        ],
        progress: [
            "Progress Tracker se apni improvement dekh sakte ho. Quick Links mein hai.",
        ],
        motivation: [
            "Tum socho usse zyada strong ho! Har rep progress hai. 💪",
            "Champions wahan bante hain jahan chhodna chahte hain. Ruko mat!",
            "Koi bura workout nahi hota — bas aana zaroori hai!",
            "Apna future self aaj ki mehnat ke liye shukriya ada karega.",
            "Dard temporary hai, chhodna permanent hota hai. Karo!",
        ],
        plan: [
            "Aapka AI workout plan Dashboard par roz dikhta hai.",
            "Tumhare goal aur experience ke hisab se personalised plan banaya gaya hai.",
        ],
        rest: [
            "Rest day bahut zaroori hai! Muscles recovery ke dauran grow karte hain.",
            "Aaj rest karo? Bilkul sahi. Recovery bhi training ka hissa hai. 🌿",
        ],
        default: [
            "Main aapka SmartGym AI coach hoon! Workout, diet, BMI ke baare mein poochho.",
            "Poochho: 'Aaj ka workout kya hai?' ya 'Mujhe motivate karo'!",
        ],
    },
};

// ── Response Logic ─────────────────────────────────────────────────────────
function getResponse(text) {
    const t   = text.toLowerCase();
    const kb  = KB[currentLang];
    const pick = arr => arr[Math.floor(Math.random() * arr.length)];

    if (/hello|hi|hey|namaste|namaskar|kya haal/.test(t)) return pick(kb.greeting);
    if (/workout|exercise|train|gym|kya karna|aaj ka/.test(t))  return pick(kb.workout);
    if (/bmi|weight|height|wazan|lambaai/.test(t))              return pick(kb.bmi);
    if (/diet|food|nutrition|meal|eat|khaana|khana/.test(t))    return pick(kb.diet);
    if (/calorie|protein|macro|calori/.test(t))                 return pick(kb.calorie);
    if (/calendar|log|date|history|cal/.test(t))                return pick(kb.calendar);
    if (/progress|track|improvement|streak/.test(t))            return pick(kb.progress);
    if (/motivat|inspire|push|boost|hausla|himmat|cheer/.test(t)) return pick(kb.motivation);
    if (/plan|routine|schedule|program/.test(t))                return pick(kb.plan);
    if (/rest|recover|sleep|aram/.test(t))                      return pick(kb.rest);
    if (/strength|strong|power|1rm|bench/.test(t))              return pick(kb.strength || kb.workout);
    if (/admin|trainer|coach/.test(t) && kb.admin)              return pick(kb.admin);
    return pick(kb.default);
}

// ── TTS ────────────────────────────────────────────────────────────────────
function speak(text) {
    if (!synth) return;
    synth.cancel();
    const utter  = new SpeechSynthesisUtterance(text);
    utter.lang   = currentLang === 'hi' ? 'hi-IN' : 'en-IN';
    utter.rate   = 1.0;
    utter.pitch  = 1.0;
    utter.volume = 1.0;
    // Prefer a local voice if available
    const voices = synth.getVoices();
    const langCode = utter.lang;
    const preferred = voices.find(v => v.lang === langCode) ||
                      voices.find(v => v.lang.startsWith(langCode.split('-')[0]));
    if (preferred) utter.voice = preferred;
    synth.speak(utter);
}

// ── STT ────────────────────────────────────────────────────────────────────
function createRecognition() {
    const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRec) return null;

    const rec          = new SpeechRec();
    rec.lang           = currentLang === 'hi' ? 'hi-IN' : 'en-IN';
    rec.interimResults = false;
    rec.maxAlternatives = 1;
    rec.continuous     = false;

    rec.onstart = () => {
        setListening(true);
        setResponse(currentLang === 'hi' ? '🎤 Sun raha hoon...' : '🎤 Listening...');
    };

    rec.onresult = (e) => {
        const transcript = e.results[0][0].transcript;
        setResponse(`🗣️ "${transcript}"`);
        setTimeout(() => {
            const reply = getResponse(transcript);
            setResponse(`🤖 ${reply}`);
            speak(reply);
        }, 700);
    };

    rec.onerror = (e) => {
        const msgs = {
            'no-speech':   currentLang === 'hi' ? 'Kuch suna nahi, dobara bolo.' : 'No speech detected. Try again.',
            'not-allowed': currentLang === 'hi' ? 'Mic permission deny hai.' : 'Microphone access denied.',
            'network':     'Network error. Please check connection.',
        };
        setResponse(`⚠️ ${msgs[e.error] || 'Error: ' + e.error}`);
        stopListening();
    };

    rec.onend = () => stopListening();
    return rec;
}

// ── Controls ───────────────────────────────────────────────────────────────
function toggleVoice() {
    if (isListening) { stopListening(); return; }
    startListening();
}

function startListening() {
    recognition = createRecognition();
    if (!recognition) {
        setResponse('⚠️ Voice not supported. Please use Chrome or Edge.');
        return;
    }
    try {
        recognition.start();
    } catch (e) {
        setResponse('⚠️ Could not start microphone. Try refreshing.');
    }
}

function stopListening() {
    if (recognition) { try { recognition.stop(); } catch (_) {} }
    recognition  = null;
    setListening(false);
}

function setListening(state) {
    isListening = state;
    if (state) {
        btn.textContent = '🔴 Stop';
        btn.classList.add('listening');
        document.getElementById('va-mic-icon').textContent = '🔴';
    } else {
        btn.textContent = '🎤 Ask Coach';
        btn.classList.remove('listening');
        document.getElementById('va-mic-icon').textContent = '🎤';
    }
}

function setResponse(text) {
    if (responseEl) {
        responseEl.style.opacity = '0';
        setTimeout(() => {
            responseEl.textContent  = text;
            responseEl.style.opacity = '1';
            responseEl.style.transition = '.3s';
        }, 150);
    }
}

// ── Language Toggle ─────────────────────────────────────────────────────────
function toggleLang() {
    currentLang = currentLang === 'en' ? 'hi' : 'en';
    langBtn.textContent = currentLang === 'hi' ? '🌐 HI' : '🌐 EN';
    const msg = currentLang === 'hi'
        ? 'Hindi mode on! Poochho: "Aaj ka workout kya hai?"'
        : 'English mode on! Ask: "What\'s my workout today?"';
    setResponse(msg);
    speak(msg);
    if (isListening) stopListening();
}

// ── Keyboard Shortcut (Space bar toggle) ───────────────────────────────────
document.addEventListener('keydown', (e) => {
    if (e.code === 'Space' && e.shiftKey) {
        e.preventDefault();
        toggleVoice();
    }
});

// ── Init ───────────────────────────────────────────────────────────────────
(function init() {
    if (!responseEl) return;
    // Pre-load voices
    if (synth) synth.getVoices();
})();
