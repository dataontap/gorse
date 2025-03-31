
package com.example.yourapp

import android.Manifest
import android.os.Build
import android.os.Bundle
import android.view.View
import android.widget.Button
import android.widget.ProgressBar
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity

class MainActivity : AppCompatActivity() {
    private lateinit var esimManager: EsimManager
    private lateinit var requestButton: Button
    private lateinit var progressBar: ProgressBar

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)
        
        // Initialize views
        requestButton = findViewById(R.id.requestEsimButton)
        progressBar = findViewById(R.id.progressBar)
        
        // Initialize the manager
        esimManager = EsimManager { success, message ->
            runOnUiThread {
                progressBar.visibility = View.GONE
                requestButton.isEnabled = true
                Toast.makeText(this, message, Toast.LENGTH_LONG).show()
            }
        }
        
        // Request runtime permissions
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
            requestPermissions(arrayOf(Manifest.permission.READ_PHONE_STATE), 1)
        }
        
        // Add button click listener
        requestButton.setOnClickListener {
            requestButton.isEnabled = false
            progressBar.visibility = View.VISIBLE
            esimManager.requestEsim(this)
        }
    }

    override fun onRequestPermissionsResult(
        requestCode: Int,
        permissions: Array<out String>,
        grantResults: IntArray
    ) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults)
        // Handle permission results if needed
    }
}
