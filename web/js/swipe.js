function Swipe(element, minDelta = 15) {
    this.element = element
    this.element.addEventListener('touchstart', (e) => this.TouchStart(e))
    this.element.addEventListener('touchend', (e) => this.TouchEnd(e))
    this.element.addEventListener('touchmove', (e) => this.TouchMove(e))
    this.onStart = () => {}
    this.onEnd = () => {}
}

Swipe.prototype.TouchStart = function(e) {
    this.startX = e.touches[0].clientX
    this.startY = e.touches[0].clientY
    this.element.classList.remove('swipe-animated')
}

Swipe.prototype.TouchMove = function(e) {
    this.deltaX = e.touches[0].clientX - this.startX
    this.deltaY = e.touches[0].clientY - this.startY

    if (Math.abs(this.deltaX) < Math.abs(this.deltaY))
        return

    e.preventDefault()
    this.onStart()

    if (this.deltaX > 0)
        this.startX += this.deltaX

    this.element.style.transform = `translateX(${Math.min(0, this.deltaX)}px)`
}

Swipe.prototype.TouchEnd = function(e) {
    this.element.classList.add('swipe-animated')
    let swiped = Math.abs(this.deltaX) > this.element.clientWidth / 2

    if (!swiped)
        this.element.style.transform = `translateX(0)`

    this.onEnd(swiped)
}