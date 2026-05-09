package com.calculator.app

import android.animation.AnimatorSet
import android.animation.ObjectAnimator
import android.animation.ValueAnimator
import android.os.Bundle
import android.view.View
import android.view.animation.AccelerateDecelerateInterpolator
import android.view.animation.BounceInterpolator
import android.view.animation.OvershootInterpolator
import android.widget.Button
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.ContextCompat
import com.calculator.app.databinding.ActivityMainBinding
import kotlin.math.sqrt

class MainActivity : AppCompatActivity() {

    private lateinit var binding: ActivityMainBinding

    private var currentInput = StringBuilder()
    private var operator = ""
    private var firstOperand = 0.0
    private var isNewOperation = false
    private var hasDecimal = false
    private var lastResult = ""

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityMainBinding.inflate(layoutInflater)
        setContentView(binding.root)

        setupButtons()
        updateDisplay("0")
    }

    private fun setupButtons() {
        // Цифры
        val numberButtons = listOf(
            binding.btn0, binding.btn1, binding.btn2, binding.btn3,
            binding.btn4, binding.btn5, binding.btn6, binding.btn7,
            binding.btn8, binding.btn9
        )

        numberButtons.forEach { button ->
            button.setOnClickListener {
                animateButtonPress(it)
                onNumberClick(button.text.toString())
            }
        }

        // Операторы
        binding.btnAdd.setOnClickListener {
            animateOperatorPress(it)
            onOperatorClick("+")
        }
        binding.btnSubtract.setOnClickListener {
            animateOperatorPress(it)
            onOperatorClick("-")
        }
        binding.btnMultiply.setOnClickListener {
            animateOperatorPress(it)
            onOperatorClick("×")
        }
        binding.btnDivide.setOnClickListener {
            animateOperatorPress(it)
            onOperatorClick("÷")
        }

        // Специальные кнопки
        binding.btnEquals.setOnClickListener {
            animateEqualsPress(it)
            onEqualsClick()
        }
        binding.btnClear.setOnClickListener {
            animateClearPress(it)
            onClearClick()
        }
        binding.btnDelete.setOnClickListener {
            animateButtonPress(it)
            onDeleteClick()
        }
        binding.btnDecimal.setOnClickListener {
            animateButtonPress(it)
            onDecimalClick()
        }
        binding.btnPlusMinus.setOnClickListener {
            animateButtonPress(it)
            onPlusMinusClick()
        }
        binding.btnPercent.setOnClickListener {
            animateButtonPress(it)
            onPercentClick()
        }
    }

    // ==================== ЛОГИКА КАЛЬКУЛЯТОРА ====================

    private fun onNumberClick(number: String) {
        if (isNewOperation) {
            currentInput.clear()
            hasDecimal = false
            isNewOperation = false
        }

        if (currentInput.toString() == "0" && number != ".") {
            currentInput.clear()
        }

        if (currentInput.length < 12) {
            currentInput.append(number)
            updateDisplay(currentInput.toString())
        }

        animateDisplayUpdate()
    }

    private fun onOperatorClick(op: String) {
        if (currentInput.isNotEmpty() && operator.isNotEmpty() && !isNewOperation) {
            calculateResult()
        }

        if (currentInput.isNotEmpty() || lastResult.isNotEmpty()) {
            firstOperand = if (isNewOperation && lastResult.isNotEmpty()) {
                lastResult.toDoubleOrNull() ?: 0.0
            } else {
                currentInput.toString().toDoubleOrNull() ?: 0.0
            }
            operator = op
            isNewOperation = true
            hasDecimal = false
            updateOperatorDisplay(op)
            animateOperatorHighlight()
        }
    }

    private fun onEqualsClick() {
        if (operator.isNotEmpty() && currentInput.isNotEmpty()) {
            calculateResult()
            operator = ""
            animateResultAppear()
        }
    }

    private fun calculateResult() {
        val secondOperand = currentInput.toString().toDoubleOrNull() ?: return

        val result = when (operator) {
            "+" -> firstOperand + secondOperand
            "-" -> firstOperand - secondOperand
            "×" -> firstOperand * secondOperand
            "÷" -> {
                if (secondOperand == 0.0) {
                    showError("Ошибка: деление на 0")
                    return
                }
                firstOperand / secondOperand
            }
            else -> return
        }

        val formattedResult = formatResult(result)
        lastResult = formattedResult
        currentInput.clear()
        currentInput.append(formattedResult)
        hasDecimal = formattedResult.contains(".")
        isNewOperation = true

        updateDisplay(formattedResult)
        updateOperatorDisplay("")
    }

    private fun formatResult(result: Double): String {
        return if (result == result.toLong().toDouble()) {
            result.toLong().toString()
        } else {
            val formatted = "%.10f".format(result).trimEnd('0').trimEnd('.')
            if (formatted.length > 12) {
                "%.6g".format(result)
            } else {
                formatted
            }
        }
    }

    private fun onClearClick() {
        currentInput.clear()
        operator = ""
        firstOperand = 0.0
        isNewOperation = false
        hasDecimal = false
        lastResult = ""
        updateDisplay("0")
        updateOperatorDisplay("")
        binding.tvExpression.text = ""
    }

    private fun onDeleteClick() {
        if (currentInput.isNotEmpty() && !isNewOperation) {
            val lastChar = currentInput.last()
            if (lastChar == '.') hasDecimal = false
            currentInput.deleteCharAt(currentInput.length - 1)
            if (currentInput.isEmpty()) {
                updateDisplay("0")
            } else {
                updateDisplay(currentInput.toString())
            }
        }
    }

    private fun onDecimalClick() {
        if (isNewOperation) {
            currentInput.clear()
            currentInput.append("0")
            isNewOperation = false
        }
        if (!hasDecimal) {
            if (currentInput.isEmpty()) currentInput.append("0")
            currentInput.append(".")
            hasDecimal = true
            updateDisplay(currentInput.toString())
        }
    }

    private fun onPlusMinusClick() {
        if (currentInput.isNotEmpty() && currentInput.toString() != "0") {
            if (currentInput.startsWith("-")) {
                currentInput.deleteCharAt(0)
            } else {
                currentInput.insert(0, "-")
            }
            updateDisplay(currentInput.toString())
        }
    }

    private fun onPercentClick() {
        val value = currentInput.toString().toDoubleOrNull() ?: return
        val result = value / 100
        val formatted = formatResult(result)
        currentInput.clear()
        currentInput.append(formatted)
        hasDecimal = formatted.contains(".")
        updateDisplay(formatted)
    }

    // ==================== ОБНОВЛЕНИЕ UI ====================

    private fun updateDisplay(text: String) {
        binding.tvDisplay.text = text
        adjustTextSize(text)
    }

    private fun updateOperatorDisplay(op: String) {
        val expr = if (op.isNotEmpty()) {
            "${formatResult(firstOperand)} $op"
        } else ""
        binding.tvExpression.text = expr
    }

    private fun adjustTextSize(text: String) {
        val size = when {
            text.length > 10 -> 36f
            text.length > 7 -> 48f
            else -> 64f
        }
        binding.tvDisplay.textSize = size
    }

    private fun showError(message: String) {
        updateDisplay("Ошибка")
        binding.tvExpression.text = message
        currentInput.clear()
        operator = ""
        isNewOperation = true
        animateError()
    }

    // ==================== АНИМАЦИИ ====================

    private fun animateButtonPress(view: View) {
        val scaleDownX = ObjectAnimator.ofFloat(view, "scaleX", 1f, 0.88f)
        val scaleDownY = ObjectAnimator.ofFloat(view, "scaleY", 1f, 0.88f)
        val scaleUpX = ObjectAnimator.ofFloat(view, "scaleX", 0.88f, 1f)
        val scaleUpY = ObjectAnimator.ofFloat(view, "scaleY", 0.88f, 1f)

        scaleDownX.duration = 80
        scaleDownY.duration = 80
        scaleUpX.duration = 150
        scaleUpY.duration = 150

        scaleUpX.interpolator = OvershootInterpolator(2f)
        scaleUpY.interpolator = OvershootInterpolator(2f)

        val pressSet = AnimatorSet()
        pressSet.playTogether(scaleDownX, scaleDownY)

        val releaseSet = AnimatorSet()
        releaseSet.playTogether(scaleUpX, scaleUpY)
        releaseSet.startDelay = 80

        val fullSet = AnimatorSet()
        fullSet.playSequentially(pressSet, releaseSet)
        fullSet.start()

        // Эффект пульсации тени
        val elevationDown = ObjectAnimator.ofFloat(view, "elevation", 8f, 2f)
        val elevationUp = ObjectAnimator.ofFloat(view, "elevation", 2f, 8f)
        elevationDown.duration = 80
        elevationUp.duration = 150
        elevationUp.startDelay = 80

        AnimatorSet().apply {
            playSequentially(elevationDown, elevationUp)
            start()
        }
    }

    private fun animateOperatorPress(view: View) {
        // Вращение + масштаб
        val rotate = ObjectAnimator.ofFloat(view, "rotation", 0f, -8f, 8f, 0f)
        rotate.duration = 300
        rotate.interpolator = AccelerateDecelerateInterpolator()

        val scaleX = ObjectAnimator.ofFloat(view, "scaleX", 1f, 0.85f, 1.1f, 1f)
        val scaleY = ObjectAnimator.ofFloat(view, "scaleY", 1f, 0.85f, 1.1f, 1f)
        scaleX.duration = 300
        scaleY.duration = 300

        AnimatorSet().apply {
            playTogether(rotate, scaleX, scaleY)
            start()
        }
    }

    private fun animateEqualsPress(view: View) {
        // Прыжок кнопки
        val scaleX = ObjectAnimator.ofFloat(view, "scaleX", 1f, 0.9f, 1.15f, 1f)
        val scaleY = ObjectAnimator.ofFloat(view, "scaleY", 1f, 0.9f, 1.15f, 1f)
        scaleX.duration = 400
        scaleY.duration = 400
        scaleX.interpolator = BounceInterpolator()
        scaleY.interpolator = BounceInterpolator()

        AnimatorSet().apply {
            playTogether(scaleX, scaleY)
            start()
        }
    }

    private fun animateClearPress(view: View) {
        // Дрожание кнопки очистки
        val shake = ObjectAnimator.ofFloat(
            view, "translationX",
            0f, -15f, 15f, -12f, 12f, -8f, 8f, -4f, 4f, 0f
        )
        shake.duration = 400
        shake.interpolator = AccelerateDecelerateInterpolator()
        shake.start()

        val scaleX = ObjectAnimator.ofFloat(view, "scaleX", 1f, 0.9f, 1f)
        val scaleY = ObjectAnimator.ofFloat(view, "scaleY", 1f, 0.9f, 1f)
        scaleX.duration = 200
        scaleY.duration = 200

        AnimatorSet().apply {
            playTogether(scaleX, scaleY)
            start()
        }
    }

    private fun animateDisplayUpdate() {
        val flash = ObjectAnimator.ofFloat(binding.tvDisplay, "alpha", 1f, 0.6f, 1f)
        flash.duration = 100
        flash.start()
    }

    private fun animateResultAppear() {
        // Красивое появление результата
        binding.tvDisplay.apply {
            alpha = 0f
            scaleX = 0.7f
            scaleY = 0.7f
        }

        val alpha = ObjectAnimator.ofFloat(binding.tvDisplay, "alpha", 0f, 1f)
        val scaleX = ObjectAnimator.ofFloat(binding.tvDisplay, "scaleX", 0.7f, 1f)
        val scaleY = ObjectAnimator.ofFloat(binding.tvDisplay, "scaleY", 0.7f, 1f)

        alpha.duration = 300
        scaleX.duration = 300
        scaleY.duration = 300

        scaleX.interpolator = OvershootInterpolator(1.5f)
        scaleY.interpolator = OvershootInterpolator(1.5f)

        AnimatorSet().apply {
            playTogether(alpha, scaleX, scaleY)
            start()
        }
    }

    private fun animateOperatorHighlight() {
        val colorFrom = ContextCompat.getColor(this, R.color.display_bg)
        val colorTo = ContextCompat.getColor(this, R.color.operator_highlight)

        val colorAnimator = ValueAnimator.ofArgb(colorFrom, colorTo, colorFrom)
        colorAnimator.duration = 400
        colorAnimator.addUpdateListener { animator ->
            binding.tvExpression.setBackgroundColor(animator.animatedValue as Int)
        }
        colorAnimator.start()
    }

    private fun animateError() {
        val shake = ObjectAnimator.ofFloat(
            binding.tvDisplay, "translationX",
            0f, -20f, 20f, -15f, 15f, -10f, 10f, 0f
        )
        shake.duration = 500
        shake.start()
    }
}
