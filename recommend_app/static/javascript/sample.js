// キャンバスの設定
var fgCanvas = document.getElementById('fgCanvas');
var bgCanvas = document.getElementById('bgCanvas');

var fgContext = fgCanvas.getContext('2d');
var bgContext = bgCanvas.getContext('2d');

const offset = 2400;
const scale = 1200;
const imgSize = 48;
const font = '18px sans-serif';

fgCanvas.height = offset * 2;
fgCanvas.width = offset * 2;

bgCanvas.height = offset * 2;
bgCanvas.width = offset * 2;

fgContext.font = font;
fgContext.textBaseline = 'top';

bgContext.font = font;
bgContext.textBaseline = 'top';

// 初期データの取得
var dataTransformed, dataId
var currentId = -1;
var useIndex = 0;

// フォームを追加
form_num = 1;
document.getElementById("add_form").addEventListener('click', function() {
    var input_data = document.createElement('input');
    input_data.type = 'text';
    input_data.id = 'inputform_' + form_num;
    var parent = document.getElementById('form_area');
    parent.appendChild(input_data);
    form_num++;
});

// プレイリスト情報を取得
document.getElementById("submit_button").addEventListener('click', function () {
    var playlist_id = [];
    for (let i = 0; i < form_num; i++) {
        playlist_id.push(document.getElementById('inputform_' + i).value);
    }

    fetch('/playlist_id', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(playlist_id)
    })
    .then(response => response.json())
    .then(responseData => {
        console.log('Response from server:', responseData.transformed);

        document.getElementById("form_wrapper").style.display = "none";
        document.getElementById("canvas_wrapper").style.display = "block";
        fetchData();
    })
    .catch(error => console.error('Error:', error));
});

// 格子状の線を描画
for (let i = -50; i < 50; i++) {
    var interval = scale/10;

    fgContext.strokeStyle = '#363636';
    fgContext.lineWidth = 1;

    fgContext.beginPath();
    fgContext.moveTo(offset + interval * i, offset*2);
    fgContext.lineTo(offset + interval * i, 0);
    fgContext.stroke();
    fgContext.closePath();

    fgContext.beginPath();
    fgContext.moveTo(0, offset + interval * i);
    fgContext.lineTo(offset*2, offset + interval * i);
    fgContext.stroke();
    fgContext.closePath();
}

// クリック時にポップアップを表示
fgCanvas.addEventListener('click', function (event) {
    var rect = event.target.getBoundingClientRect();
    var x = event.clientX - rect.left;
    var y = event.clientY - rect.top;

    for (let i = 0; i < dataTransformed.length; i++) {
        if (
            Math.abs(x - (offset + scale * dataTransformed[i].x)) < imgSize/2 &&
            Math.abs(y - (offset + scale * dataTransformed[i].y)) < imgSize/2
        ) {
            document.getElementById("track_name").innerHTML = dataId[i].track_name;
            document.getElementById("artist_name").innerHTML = dataId[i].artist_name;
            document.getElementById("jacket").src = dataId[i].url;
            document.getElementById("popup").style.left = offset + scale * dataTransformed[i].x + imgSize + "px";
            document.getElementById("popup").style.top = offset + scale * dataTransformed[i].y - imgSize/2 + "px";
            document.getElementById("popup").style.display = "block";
            currentId = i
        }
    }
});

// クリック時に類似曲を表示
document.getElementById("search_track").addEventListener('click', function () {
    fetch('/run_function', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(currentId)
    })
    .then(response => response.json())
    .then(responseData => {
        console.log('Response fgom server:', responseData.transformed);

        fetchData();
    })
    .catch(error => console.error('Error:', error));
});

// 要素を取得してプロットする関数
function fetchData() {
    fetch('/data')
    .then(response => response.json())
    .then(dataframe => {
        console.log(dataframe)

        function getColorForUserId(userId) {
            const colors = [
                'rgb(220, 100, 100)',
                'rgb(100, 220, 100)',
                'rgb(100, 100, 220)',
                'rgb(220, 220, 100)',
                'rgb(100, 220, 220)',
                'rgb(220, 100, 220)',
            ]
            return colors[userId] || 'black';
        }

        dataTransformed = dataframe.transformed;
        dataId = dataframe.id;

        for (let i = useIndex; i < dataTransformed.length; i++) {
            bgContext.strokeStyle = getColorForUserId(dataId[i].UserId);
            bgContext.lineWidth = 2;

            function lazyDrawImage(i) {
                return function() {


                    var image = new Image();
                    image.src = dataId[i].url;
                    image.onload = function() {
                        if(dataId[i].recommendId != -1) {
                            bgContext.beginPath();
                            bgContext.moveTo(
                                offset + scale * dataTransformed[dataId[i].recommendId].x,
                                offset + scale * dataTransformed[dataId[i].recommendId].y
                            );
                            bgContext.lineTo(
                                offset + scale * dataTransformed[i].x,
                                offset + scale * dataTransformed[i].y
                            );
                            bgContext.stroke();
                            bgContext.closePath();
                        }

                        fgContext.strokeStyle = getColorForUserId(dataId[i].UserId);
                        fgContext.lineWidth = 2;
                        fgContext.strokeRect(
                            offset + scale * dataTransformed[i].x - imgSize/2,
                            offset + scale * dataTransformed[i].y - imgSize/2,
                            imgSize,
                            imgSize
                        );

                        fgContext.drawImage(
                            image,
                            offset + scale * dataTransformed[i].x - imgSize/2,
                            offset + scale * dataTransformed[i].y - imgSize/2,
                            imgSize,
                            imgSize
                        );
                    };
                }
            }

            lazyDrawImage(i)();
        }

        useIndex = dataTransformed.length;
    })
    .catch(error => console.error('Error fetching data:', error));
}