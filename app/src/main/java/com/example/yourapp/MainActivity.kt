
package com.example.yourapp

import android.Manifest
import android.os.Build
import android.os.Bundle
import android.view.View
import android.widget.Button
import android.widget.ProgressBar
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import androidx.core.app.ActivityCompat

class MainActivity : AppCompatActivity() {
    private lateinit var activateButton: Button
    private lateinit var progressBar: ProgressBar
    private lateinit var statusText: TextView
    private val esimManager = EsimManager { success, message ->
        runOnUiThread {
            handleEsimResponse(success, message)
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        activateButton = findViewById(R.id.activateButton)
        progressBar = findViewById(R.id.progressBar)
        statusText = findViewById(R.id.statusText)

        activateButton.setOnClickListener {
            requestPermissions()
        }
    }

    private fun requestPermissions() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
            ActivityCompat.requestPermissions(
                this,
                arrayOf(Manifest.permission.READ_PHONE_STATE),
                PERMISSION_REQUEST_CODE
            )
        }
    }

    private fun handleEsimResponse(success: Boolean, message: String) {
        progressBar.visibility = View.GONE
        activateButton.isEnabled = true
        statusText.text = message
        statusText.setTextColor(if (success) 
            getColor(android.R.color.holo_green_dark)
        else 
            getColor(android.R.color.holo_red_dark))
    }

    override fun onRequestPermissionsResult(
        requestCode: Int,
        permissions: Array<out String>,
        grantResults: IntArray
    ) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults)
        if (requestCode == PERMISSION_REQUEST_CODE) {
            progressBar.visibility = View.VISIBLE
            activateButton.isEnabled = false
            statusText.text = "Requesting eSIM activation..."
            esimManager.requestEsim(this)
        }
    }

    companion object {
        private const val PERMISSION_REQUEST_CODE = 123
    }
}
