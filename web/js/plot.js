function Plot(padding = 5, paddingBottom = 20, minWidth = 10, steps = 40, lineClass="plot-line", areaClass = "plot-area") {
    this.padding = padding
    this.paddingBottom = paddingBottom
    this.minWidth = minWidth
    this.steps = steps

    this.lineClass = lineClass
    this.areaClass = areaClass
}

Plot.prototype.ExtractKey = function(value) {
    if (value.toString().match(/^\d\d?\.\d\d?\.\d{4}$/g)) {
        let [day, month, year] = value.split('.')
        return new Date(+year, +month - 1, +day)
    }

    return value
}

Plot.prototype.GetDelta = function(x1, x2) {
    let delta = x1 - x2

    if (x1 instanceof Date)
        return Math.ceil(delta / (1000 * 60 * 60 * 24))

    return delta
}

Plot.prototype.PreprocessX = function(x) {
    let max = this.GetDelta(x[x.length - 1], x[0])
    let min = Infinity

    for (let i = 1; i < x.length; i++) {
        min = Math.min(min, this.GetDelta(x[i], x[i - 1]))
        x[i] = this.GetDelta(x[i], x[0]) / max
    }

    x[0] = 0

    return {x, min, max}
}

Plot.prototype.PreprocessY = function(y) {
    let min = y[0]
    let max = y[0]

    for (let yi of y) {
        min = Math.min(min, yi)
        max = Math.max(max, yi)
    }

    let delta = max - min

    if (Math.abs(delta) < 1e-8) {
        min -= 0.5
        max += 0.5
    }
    else {
        min -= 0.05 * delta
        max += 0.05 * delta
    }

    return {min, max}
}

Plot.prototype.Interpolate = function(xi, x, y) {
    if (x.length == 2)
        return y[0] + (y[1] - y[0]) * (xi - x[0]) / (x[1] - x[0])

    let result = 0
    let sumWeights = 0

    for (let i = 0; i < x.length; i++) {
        let distance = Math.abs(xi - x[i])

        if (distance === 0)
            return y[i]

        let weight = 1 / Math.pow(distance, 2)
        result += y[i] * weight
        sumWeights += weight
    }

    return result / sumWeights
}

Plot.prototype.AppendLabel = function(svg, x, y, labelText, align = "middle", baseline = "middle", rotation = null) {
    let label = document.createElementNS('http://www.w3.org/2000/svg', "text")
    label.textContent = labelText
    label.setAttribute("x", x)
    label.setAttribute("y", y)
    label.setAttribute("alignment-baseline", baseline)
    label.setAttribute("text-anchor", align)
    label.setAttribute("class", "label")

    if (rotation !== null)
        label.setAttribute("transform", `rotate(90, ${x}, ${y})`)

    svg.appendChild(label)
    return label
}

Plot.prototype.MakePoint = function(radius, x, y) {
    return `M${x} ${y} m ${-radius}, 0 a ${radius},${radius} 0 1,0 ${radius*2},0 a ${radius},${radius} 0 1,0 ${-radius*2},0`
}

Plot.prototype.Plot = function(svg, data, className = "plot-color", keyX = "date", keyY = "value") {
    svg.innerHTML = ''
    svg.style.width = null

    let dataX = data.map((dataItem) => this.ExtractKey(dataItem[keyX]))
    let dataY = data.map((dataItem) => this.ExtractKey(dataItem[keyY]))

    let infoX = this.PreprocessX(dataX)
    let infoY = this.PreprocessY(dataY)

    let width = svg.clientWidth
    let height = svg.clientHeight

    let deltaWidth = (width - this.padding * 2) / infoX.min

    if (deltaWidth < this.minWidth) {
        width *= this.minWidth / deltaWidth
        svg.style.width = `${width}px`
    }

    let viewWidth = (width - this.padding * 2)
    let viewHeight = (height - this.padding - this.paddingBottom) / (infoY.max - infoY.min)

    let points = []
    let linePoints = []
    let areaPoints = [`M${this.padding} ${height - this.paddingBottom}`]

    for (let i = 1; i < data.length; i++) {
        for (let j = 0; j < this.steps; j++) {
            let t = j / (this.steps - 1)
            let xi = infoX.x[i - 1] * (1 - t) + infoX.x[i] * t
            let yi = this.Interpolate(xi, infoX.x, dataY)

            let x = this.padding + xi * viewWidth
            let y = this.padding + (infoY.max - yi) * viewHeight

            linePoints.push(`${linePoints.length == 0 ? 'M' : 'L'}${x} ${y}`)
            areaPoints.push(`L${x} ${y}`)

            if (i == 1 && j == 0 || j == this.steps - 1) {
                points.push({x: x, y: y})
                linePoints.push(this.MakePoint(2, x, y))
                linePoints.push(this.MakePoint(1, x, y))
            }
        }
    }

    areaPoints.push(`L${width - this.padding} ${height - this.paddingBottom}`)

    let areaPath = document.createElementNS('http://www.w3.org/2000/svg', "path")
    areaPath.setAttribute("d", areaPoints.join(" "))
    areaPath.setAttribute("class", this.areaClass)
    svg.appendChild(areaPath)

    let linePath = document.createElementNS('http://www.w3.org/2000/svg', "path")
    linePath.setAttribute("d", linePoints.join(" "))
    linePath.setAttribute("class", this.lineClass)
    svg.appendChild(linePath)

    for (let i = 0; i < data.length; i++) {
        let x = points[i].x
        let y = points[i].y
        let align = i == 0 ? 'start' : i == data.length - 1 ? 'end' : 'middle'
        let baseline = i == 0 ? 'after-edge' : i == data.length - 1 ? 'before-edge' : 'middle'

        this.AppendLabel(svg, x, y, data[i][keyY], align, "after-edge")
        this.AppendLabel(svg, x, height - this.paddingBottom + 1, data[i][keyX], "start", baseline, 90)
    }

    svg.setAttribute("viewBox", `0 0 ${width} ${height}`)
}