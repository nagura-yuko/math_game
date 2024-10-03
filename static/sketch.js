let canvas;
let problems = [];
let currentProblemIndex = 0;
let currentAnswer = null;
let currentProblemText = '';
let correctCount = 0;
let incorrectCount = 0;
let incorrectProblems = [];
let answered = false;

function setup() {
    console.log("setup関数が実行されました");

    try {
        pixelDensity(1);
        canvas = createCanvas(280, 280);
        canvas.parent('canvas-area');
        background(255);
        console.log("キャンバスが正常に作成されました。");
    } catch (error) {
        console.error("キャンバスの作成中にエラーが発生しました: ", error);
    }

    document.getElementById("operation-selection").style.display = "block";
    document.getElementById("problem-area").style.display = "none";
    document.getElementById("canvas-area").style.display = "none";
    document.getElementById("buttons").style.display = "none";
    document.getElementById("next-btn").style.display = "none";
    document.getElementById("reset-btn").style.display = "none";
}

function preload() {
    console.log("preload関数が実行されました。問題データをロード中...");
}

function selectOperation(operation) {
    // 問題選択ボタンを非表示にし、問題エリアとキャンバスを表示
    document.getElementById("operation-selection").style.display = "none";
    document.getElementById("problem-area").style.display = "block";
    document.getElementById("canvas-area").style.display = "block";
    document.getElementById("buttons").style.display = "block";

     // ボタンエリアを横並びにするために display: flex を適用
    const buttonsArea = document.getElementById("buttons");
    buttonsArea.style.display = "flex";  // 横並びにする
    buttonsArea.style.justifyContent = "center";  // ボタンを中央に配置
    buttonsArea.style.gap = "10px";  // ボタン間のスペースを設定


    const url = `/get_csv_files?operation=${operation}`;
    
    fetch(url)
        .then(response => response.json())
        .then(data => {
            if (data.path) {
                console.log(`CSVファイルのロード成功: ${data.path}`);
                loadCSV(data.path);  // ロードしたCSVファイルを使って問題を読み込む
            } else {
                console.error('CSVファイルが見つかりませんでした。');
            }
        })
        .catch(error => {
            console.error('CSVファイルのロード中にエラーが発生しました: ', error);
        });
}

function loadCSV(csvPath) {
    fetch(csvPath)
        .then(response => response.text())
        .then(data => {
            console.log('CSVファイルが正常に読み込まれました');
            processCSVData(data);  // CSVデータを処理する
        })
        .catch(error => {
            console.error('CSVファイルのロード中にエラーが発生しました: ', error);
        });
}

function processCSVData(csvData) {
    let rows = csvData.split('\n').filter(row => row.trim() !== "");  // 空行を除去
    let headers = rows[0].split(',');

    let problemSet = rows.slice(1).map(row => {
        let values = row.split(',');
        let problem = {};
        headers.forEach((header, index) => {
            if (values[index]) {
                problem[header.trim()] = values[index].trim();
            }
        });
        return problem;
    });

    problems = problemSet;
    currentProblemIndex = 0;  // インデックスをリセット
    loadNextProblem();  // 最初の問題をロード
}

function loadNextProblem() {
    clearHint();
    if (problems && currentProblemIndex < problems.length) {
        let currentProblem = problems[currentProblemIndex];
        let problem1 = currentProblem["problem1"];
        let problem2 = currentProblem["problem2"];
        let symbol = currentProblem["symbol"];
        currentAnswer = currentProblem["answer"];

        currentProblemText = `${problem1} ${symbol} ${problem2}`;

        document.getElementById("problem-text").innerHTML = `<h2>${currentProblemText}</h2>`;
        currentProblemIndex++;
        answered = false;
        document.getElementById("guessbtn").style.display = "block";
        document.getElementById("clearbtn").style.display = "block";
        document.getElementById("hintbtn").style.display = "block";
        document.getElementById("next-btn").style.display = "none";
        document.getElementById("reset-btn").style.display = "none";
        canvas.style.display = "block";  // キャンバスを再表示
        clearCanvas();  // キャンバスをクリア
    } else {
        showResults();
    }
}

function mouseDragged() {
    if (mouseX < width && mouseX > 0 && mouseY < height && mouseY > 0) {
        stroke(0);
        strokeWeight(10);
        line(pmouseX, pmouseY, mouseX, mouseY);  // ドラッグ中に線を描画
    }
}

function guessAndSave() {
    if (answered) return;

    const imageData = canvas.elt.toDataURL('image/png');  // キャンバスのデータをPNG形式で取得

    fetch('/predict', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ image: imageData })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        let pred = data.prediction;
        if (pred == currentAnswer) {
            document.getElementById('predict').innerHTML = `${pred} 正解！`;
            correctCount++;
        } else {
            document.getElementById('predict').innerHTML = `${pred} 不正解！答えは ${currentAnswer} です。`;
            incorrectCount++;
            incorrectProblems.push({
                problem: currentProblemText,
                correctAnswer: currentAnswer
            });
        }
        answered = true;
        document.getElementById("guessbtn").style.display = "none";
        document.getElementById("clearbtn").style.display = "none";
        document.getElementById("hintbtn").style.display = "none";
        document.getElementById("next-btn").style.display = "block";
    })
    .catch(error => {
        console.error('Error during prediction:', error);
        document.getElementById('predict').innerHTML = 'エラーが発生しました。再度お試しください。';
    });
}


function showHint() {
    clearHint();
    let problem1 = problems[currentProblemIndex - 1]["problem1"];
    let problem2 = problems[currentProblemIndex - 1]["problem2"];
    let symbol = problems[currentProblemIndex - 1]["symbol"];

    console.log(`ヒント生成中... ${problem1} ${symbol} ${problem2}`);

    if (symbol === '＋' || symbol === '+') {
        for (let i = 0; i < problem1; i++) {
            let circle = createCircleElement();
            document.getElementById("hint-area").appendChild(circle);
        }
        for (let i = 0; i < problem2; i++) {
            let circle = createCircleElement("gray");
            document.getElementById("hint-area").appendChild(circle);
        }
    } else if (symbol === '−' || symbol === '-') {
        for (let i = 0; i < problem1 - problem2; i++) {
            let circle = createCircleElement();
            document.getElementById("hint-area").appendChild(circle);
        }
        for (let i = 0; i < problem2; i++) {
            let circle = createCircleElement("gray");
            document.getElementById("hint-area").appendChild(circle);
        }
    } else if (symbol === '×' || symbol === '*') {
        for (let i = 0; i < problem1; i++) {
            for (let j = 0; j < problem2; j++) {
                let circle = createCircleElement();
                document.getElementById("hint-area").appendChild(circle);
            }
            let br = document.createElement("br");
            document.getElementById("hint-area").appendChild(br);
        }
    } else if (symbol === '÷' || symbol === '/') {
        let quotient = Math.floor(problem1 / problem2);
        let remainder = problem1 % problem2;

        for (let i = 0; i < quotient; i++) {
            for (let j = 0; j < problem2; j++) {
                let circle = createCircleElement();
                document.getElementById("hint-area").appendChild(circle);
            }
            let br = document.createElement("br");
            document.getElementById("hint-area").appendChild(br);
        }

        if (remainder > 0) {
            for (let i = 0; i < remainder; i++) {
                let circle = createCircleElement();
                document.getElementById("hint-area").appendChild(circle);
            }
            for (let i = remainder; i < problem2; i++) {
                let circle = createCircleElement("gray");
                document.getElementById("hint-area").appendChild(circle);
            }
        }
    }
}

function createCircleElement(color = "white") {
    let circle = document.createElement("div");
    circle.className = `hint-circle ${color === "gray" ? "gray" : ""}`;
    return circle;
}

function clearHint() {
    document.getElementById("hint-area").innerHTML = '';
}

function showResults() {
    clearCanvas();
    canvas.style.display = "none";  // 結果発表時にキャンバスを非表示にする
    document.getElementById("canvas-area").style.display = "none";  // canvas-area全体を非表示にする
    document.getElementById("problem-text").innerHTML = "<h1>結果発表</h1>";

    // 結果のテーブル表示を生成
    let resultTable = "<table><tr><th>問題</th><th>答え</th><th>結果</th></tr>";
    problems.forEach((problem, index) => {
        const isCorrect = !incorrectProblems.some(incorrect => incorrect.problem === `${problem.problem1} ${problem.symbol} ${problem.problem2}`);
        resultTable += `<tr><td>${problem.problem1} ${problem.symbol} ${problem.problem2}</td><td>${problem.answer}</td><td>${isCorrect ? '正解' : '不正解'}</td></tr>`;
    });
    resultTable += "</table>";

    let resultMessage = `正解数: ${correctCount} / ${problems.length}<br>${resultTable}`;
    if (incorrectProblems.length === 0) {
        resultMessage += "全問正解です！おめでとうございます！";
    }

    document.getElementById("predict").innerHTML = resultMessage;
    document.getElementById("next-btn").style.display = "none";
    document.getElementById("reset-btn").style.display = "block";
}

function resetGame() {
    correctCount = 0;
    incorrectCount = 0;
    incorrectProblems = [];
    currentProblemIndex = 0;

    document.getElementById("predict").innerHTML = "";
    document.getElementById("problem-text").innerHTML = "";
    document.getElementById("reset-btn").style.display = "none";
    document.getElementById("guessbtn").style.display = "block";
    document.getElementById("clearbtn").style.display = "block";
    document.getElementById("hintbtn").style.display = "block";
    document.getElementById("canvas-area").style.display = "block";  // キャンバスエリア全体を再表示
    canvas.style.display = "block";  // キャンバスを再表示
    setup();  // 初期の問題選択画面に戻す
}

function clearCanvas() {
    background(255);  // キャンバスの背景を白にクリア
    document.getElementById('predict').innerHTML = '';  // 判定結果の表示をクリア
}
