function SwipeTabs(container) {
    this.container = container
    this.tabs = container.children.length
    this.tab = 0

    this.container.addEventListener("touchstart", (e) => this.TouchStart(e))
    this.container.addEventListener("touchmove", (e) => this.TouchMove(e))
    this.container.addEventListener("touchend", (e) => this.TouchEnd(e))
    this.container.addEventListener("transitionend", () => this.TransitionEnd())

    this.UpdateParams()
}

SwipeTabs.prototype.UpdateParams = function() {
    this.container.style.transform = `translateX(${-this.tab * this.container.clientWidth}px)`
    this.container.style.height = `${this.container.children[this.tab].clientHeight}px`
}

SwipeTabs.prototype.TouchStart = function(e) {
    this.startX = e.touches[0].clientX
    this.startY = e.touches[0].clientY
    this.container.style.transition = null
}

SwipeTabs.prototype.TouchMove = function(e) {
    let deltaX = e.touches[0].clientX - this.startX
    let deltaY = e.touches[0].clientY - this.startY

    if (Math.abs(deltaX) < Math.abs(deltaY) * 2 && !this.isStarted)
        return

    e.preventDefault()

    this.isStarted = true
    this.offset = this.tab * this.container.clientWidth - deltaX

    if (this.offset < 0)
        this.startX += deltaX

    this.offset = Math.max(0, Math.min(this.container.clientWidth * (this.tabs - 1), this.offset))
    this.container.style.transform = `translateX(${-this.offset}px)`
    this.container.style.transition = 'height 0.3s'
    this.container.style.height = `${this.container.children[Math.max(0, Math.min(this.tabs - 1, this.tab - Math.sign(deltaX)))].clientHeight}px`
}

SwipeTabs.prototype.TouchEnd = function(e) {
    let part = Math.min(this.offset / this.container.clientWidth, this.tabs - 1)

    this.isStarted = false
    this.tab = Math.round(part)
    this.container.style.transition = 'transform 0.15s, height 0.15s'
    this.UpdateParams()
}

SwipeTabs.prototype.TransitionEnd = function() {
    this.container.style.transition = null
}