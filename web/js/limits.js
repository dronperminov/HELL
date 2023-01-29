function GetLimits() {
    let limits = {}
    let isCorrect = true

    for (let key of ["energy", "proteins", "fats", "carbohydrates"]) {
        let input = document.getElementById(`limit-${key}`)
        let error = document.getElementById(`error-${key}`)
        let value = input.innerText.trim()

        error.innerText = ""
        input.classList.remove("error")
        input.innerText = value

        if (!IsRealValue(value) && value != "") {
            error.innerText = "Введено некорректное значение"
            input.classList.add("error")
            input.focus()
            isCorrect = false
        }
        else if (value != "") {
            limits[key] = value
            input.setAttribute("data-value", value)
        }
    }

    return isCorrect ? limits : null
}