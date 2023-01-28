function Plot(padding = 5, paddingBottom = 20, minWidth = 10, steps = 40, lineClass="plot-line", areaClass = "plot-area", axisClass = "plot-axis") {
    this.padding = padding
    this.paddingBottom = paddingBottom
    this.minWidth = minWidth
    this.steps = steps

    this.lineClass = lineClass
    this.areaClass = areaClass
    this.axisClass = axisClass
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
    if (x.length == 1)
        return {x: [0.5], min: 1, max: 1}

    let max = this.GetDelta(x[x.length - 1], x[0])
    let min = Infinity

    for (let i = 1; i < x.length; i++) {
        min = Math.min(min, this.GetDelta(x[i], x[i - 1]))
        x[i] = this.GetDelta(x[i], x[0]) / max
    }

    if (x.length == 2) {
        min = 1
        max = 1
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
    if (x.length == 1)
        return y[0]

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

Plot.prototype.GetTrend = function(x, y) {
    let sum_x = 0
    let sum_y = 0
    let sum_xx = 0
    let sum_xy = 0

    for (let i = 0; i < x.length; i++) {
        sum_x += x[i]
        sum_y += y[i]
        sum_xx += x[i] * x[i]
        sum_xy += x[i] * y[i]
    }

    let den = x.length * sum_xx - sum_x * sum_x
    let b = (sum_y * sum_xx - sum_x * sum_xy) / den
    let k = (x.length * sum_xy - sum_x * sum_y) / den

    return {k, b}
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

Plot.prototype.AddPoint = function(xi, yi, viewWidth, viewHeight, linePoints, areaPoints, points, makePoint = false) {
    let x = this.padding + xi * viewWidth
    let y = this.padding + yi * viewHeight

    linePoints.push(`${linePoints.length == 0 ? 'M' : 'L'}${x} ${y}`)
    areaPoints.push(`L${x} ${y}`)

    if (makePoint) {
        points.push({x: x, y: y})
        linePoints.push(this.MakePoint(2, x, y))
        linePoints.push(this.MakePoint(1, x, y))
    }
}

Plot.prototype.PlotTrend = function(svg, x, y, ymax, viewWidth, viewHeight) {
    let {k, b} = this.GetTrend(x, y)
    let x1 = this.padding
    let y1 = this.padding + (ymax - b) * viewHeight

    let x2 = this.padding + viewWidth
    let y2 = this.padding + (ymax - k - b) * viewHeight

    let trendPath = document.createElementNS('http://www.w3.org/2000/svg', "path")
    trendPath.setAttribute("d", `M${x1} ${y1} L${x2} ${y2}`)
    trendPath.setAttribute("class", this.lineClass)
    trendPath.setAttribute("stroke-dasharray", "4 2")
    svg.appendChild(trendPath)
}

Plot.prototype.Plot = function(svg, data, showTrend, className = "plot-color", keyX = "date", keyY = "value") {
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

    if (data.length == 1)
        this.AddPoint(infoX.x[0], infoY.max - dataY[0], viewWidth, viewHeight, linePoints, areaPoints, points, true)

    for (let i = 1; i < data.length; i++) {
        for (let j = 0; j < this.steps; j++) {
            let t = j / (this.steps - 1)
            let xi = infoX.x[i - 1] * (1 - t) + infoX.x[i] * t
            let yi = infoY.max - this.Interpolate(xi, infoX.x, dataY)
            this.AddPoint(xi, yi, viewWidth, viewHeight, linePoints, areaPoints, points, i == 1 && j == 0 || j == this.steps - 1)
        }
    }

    areaPoints.push(`L${width - this.padding} ${height - this.paddingBottom}`)

    if (data.length > 1) {
        let areaPath = document.createElementNS('http://www.w3.org/2000/svg', "path")
        areaPath.setAttribute("d", areaPoints.join(" "))
        areaPath.setAttribute("class", this.areaClass)
        svg.appendChild(areaPath)
    }

    let linePath = document.createElementNS('http://www.w3.org/2000/svg', "path")
    linePath.setAttribute("d", linePoints.join(" "))
    linePath.setAttribute("class", this.lineClass)
    svg.appendChild(linePath)

    let axisPath = document.createElementNS('http://www.w3.org/2000/svg', "path")
    axisPath.setAttribute("d", `M${this.padding} ${this.padding} L${this.padding} ${height - this.paddingBottom} L${width - this.padding} ${height - this.paddingBottom}`)
    axisPath.setAttribute("class", this.axisClass)
    svg.appendChild(axisPath)

    if (showTrend)
        this.PlotTrend(svg, infoX.x, dataY, infoY.max, viewWidth, viewHeight)

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