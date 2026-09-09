let currentFeature="Conversation";
let quizData=[];
async function api(url, body = null) {
  const options = body
    ? {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify(body)
      }
    : {};

  const response = await fetch(url, options);

  const text = await response.text();

  let data;

  try {
    data = JSON.parse(text);
  } catch (error) {
    console.error("Server returned:", text);
    throw new Error("Server returned HTML instead of JSON. Check Flask route.");
  }

  if (!response.ok) {
    throw new Error(data.error || "Request failed");
  }

  return data;
}


function openAuth(){document.getElementById("authPanel").classList.toggle("hidden")}
function setFeature(f){currentFeature=f;document.getElementById("feature").innerText=f;addBot("🤖 "+f+" mode selected.")}
function addUser(t){const d=document.createElement("div");d.className="user";d.innerText="👤 "+t;chatbox.appendChild(d);chatbox.scrollTop=chatbox.scrollHeight}
function addBot(t){const d=document.createElement("div");d.className="bot";d.innerText="🤖 "+t;chatbox.appendChild(d);chatbox.scrollTop=chatbox.scrollHeight}
const chatbox=document.getElementById("chatbox");

async function sendMessage(){
  const i=document.getElementById("message"),m=i.value.trim(); if(!m)return;
  addUser(m);i.value="";addBot("Thinking...");
  try{const d=await api("/chat",{message:m,feature:currentFeature});chatbox.lastElementChild.remove();addBot(d.answer);speak(d.answer)}
  catch(e){chatbox.lastElementChild.remove();addBot("❌ "+e.message)}
}
function speak(text){if("speechSynthesis"in window){let u=new SpeechSynthesisUtterance(text);u.lang="en-US";speechSynthesis.speak(u)}}
function startVoice(){
  const R=window.SpeechRecognition||window.webkitSpeechRecognition;
  if(!R){alert("Voice recognition is not supported. Use Chrome.");return}
  const r=new R();r.lang="en-US";r.start();r.onresult=e=>document.getElementById("message").value=e.results[0][0].transcript;
}
async function register(){try{await api("/register",{username:authUser.value,password:authPass.value});authMsg.innerText="Registered successfully!";loadMe()}catch(e){authMsg.innerText=e.message}}
async function login(){try{await api("/login",{username:authUser.value,password:authPass.value});authMsg.innerText="Login successful!";loadMe()}catch(e){authMsg.innerText=e.message}}
async function logout(){await api("/logout");location.reload()}
async function loadMe(){const d=await api("/me");if(!d.logged_in)return;profilePanel.classList.remove("hidden");language.value=d.language;level.value=d.level;authArea.innerHTML="<b>👋 "+d.username+"</b>";authPanel.classList.add("hidden")}
async function saveProfile(){try{await api("/profile",{language:language.value,level:level.value});addBot("🎯 Profile saved: "+language.value+" / "+level.value)}catch(e){addBot("❌ "+e.message)}}

async function loadQuiz(){
  setFeature("Quiz"); quizPanel.classList.remove("hidden");progressPanel.classList.add("hidden");
  quizPanel.innerHTML="<h2>🧠 Quiz</h2><p>Generating 5 questions...</p>";
  try{const d=await api("/quiz",{topic:"Vocabulary and Grammar"});quizData=d.questions;renderQuiz()}
  catch(e){quizPanel.innerHTML="<p>❌ "+e.message+"</p>"}
}
function renderQuiz(){
  quizPanel.innerHTML="<h2>🧠 Language Quiz</h2>"+quizData.map((q,i)=>`
  <div class="quiz-card"><b>${i+1}. ${q.question}</b>
  ${q.options.map((o,j)=>`<label><input type="radio" name="q${i}" value="${j}"> ${o}</label><br>`).join("")}</div>`).join("")+
  `<button onclick="submitQuiz()">Submit Quiz</button><div id="quizResult"></div>`;
}
async function submitQuiz(){
  let score=0;
  quizData.forEach((q,i)=>{let x=document.querySelector(`input[name=q${i}]:checked`);if(x&&Number(x.value)===Number(q.answer))score++});
  await api("/quiz/score",{score,total:quizData.length,topic:"Vocabulary and Grammar"});
  quizResult.innerHTML=`<div class="score">🎯 Score: ${score}/${quizData.length}</div>`;
}
async function loadProgress(){
  progressPanel.classList.remove("hidden");quizPanel.classList.add("hidden");
  try{const d=await api("/progress");
    let h="<h2>📊 My Progress</h2><h3>Activities</h3><table><tr><th>Feature</th><th>Count</th></tr>";
    d.activities.forEach(x=>h+=`<tr><td>${x.feature}</td><td>${x.n}</td></tr>`);
    h+="</table><h3>Quiz Scores</h3><table><tr><th>Topic</th><th>Score</th><th>Date</th></tr>";
    d.scores.forEach(x=>h+=`<tr><td>${x.topic}</td><td>${x.score}/${x.total}</td><td>${x.created_at}</td></tr>`);
    h+="</table><h3>Vocabulary</h3><table><tr><th>Word</th><th>Meaning</th><th>Example</th></tr>";
    d.vocabulary.forEach(x=>h+=`<tr><td>${x.word}</td><td>${x.meaning}</td><td>${x.example}</td></tr>`);
    progressPanel.innerHTML=h+"</table>";
  }catch(e){progressPanel.innerHTML="<p>❌ "+e.message+"</p>"}
}
loadMe();
