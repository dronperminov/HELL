function BarcodeScaner(id, onScan, startBtnId = "start-btn", startBoxBtnId = "start-box-btn") {
    this.codeScaner = new Html5Qrcode("reader", {experimentalFeatures: {useBarCodeDetectorIfSupported: true}})
    this.codes = {}

    this.startBtn = document.getElementById(startBtnId)
    this.startBoxBtn = document.getElementById(startBoxBtnId)

    this.startBtn.addEventListener("click", () => {this.Stop(); this.Start(false)})
    this.startBoxBtn.addEventListener("click", () => {this.Stop(); this.Start(true)})

    this.onScan = onScan
}

BarcodeScaner.prototype.Stop = function() {
    this.startBtn.classList.remove("selected")
    this.startBoxBtn.classList.remove("selected")

    try {
        this.codeScaner.stop().then((ignore) => {

        }).catch((err) => {
            
        })
    }
    catch (error) {

    }
}

BarcodeScaner.prototype.Start = function(withBox = false) {
    let config = {
        fps: 10,
        aspectRatio: 1,
        focusMode: "continuous"
    }

    if (withBox) {
        this.startBoxBtn.classList.add("selected")
        this.startBtn.classList.remove("selected")

        let width = document.getElementById("reader").clientWidth * 0.8
        config.qrbox = {width: width, height: width / 2}
    }
    else {
        this.startBtn.classList.add("selected")
        this.startBoxBtn.classList.remove("selected")
    }

    this.codeScaner.start({ facingMode: "environment" }, config, (decodedText, decodedResult) => this.OnSuccess(decodedText, decodedResult))
}

BarcodeScaner.prototype.OnSuccess = function(decodedText, decodedResult) {
    if (decodedText in this.codes)
        this.codes[decodedText]++
    else
        this.codes[decodedText] = 1

    for (let code of Object.keys(this.codes)) {
        if (this.codes[code] > 2) {
            this.codes = {}
            this.onScan(code)
            return
        }
    }
}
