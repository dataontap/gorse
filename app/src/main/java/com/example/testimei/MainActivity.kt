
package com.example.testimei

import android.Manifest
import android.content.pm.PackageManager
import android.os.Build
import android.webkit.JavascriptInterface
import android.webkit.WebView
import android.webkit.WebViewClient
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat

class MainActivity : AppCompatActivity() {
    private lateinit var webView: WebView
    private val esimManager = EsimManager { success, message ->
        runOnUiThread {
            webView.evaluateJavascript("handleEsimResponse($success, '$message')", null)
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        setupWebView()
        checkPermissions()
    }

    private fun setupWebView() {
        webView = findViewById(R.id.webView)
        webView.settings.apply {
            javaScriptEnabled = true
            domStorageEnabled = true
            databaseEnabled = true
            mixedContentMode = android.webkit.WebSettings.MIXED_CONTENT_ALWAYS_ALLOW
        }
        webView.webViewClient = WebViewClient()
        webView.addJavascriptInterface(WebAppInterface(this), "Android")
        webView.loadUrl("https://get-dot-esim.replit.app")
    }

    private fun checkPermissions() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
            if (ContextCompat.checkSelfPermission(this, Manifest.permission.READ_PHONE_STATE) 
                != PackageManager.PERMISSION_GRANTED) {
                ActivityCompat.requestPermissions(
                    this,
                    arrayOf(Manifest.permission.READ_PHONE_STATE),
                    PERMISSION_REQUEST_CODE
                )
            }
        }
    }

    override fun onRequestPermissionsResult(
        requestCode: Int,
        permissions: Array<out String>,
        grantResults: IntArray
    ) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults)
        when (requestCode) {
            PERMISSION_REQUEST_CODE -> {
                if (grantResults.isNotEmpty() && grantResults[0] == PackageManager.PERMISSION_GRANTED) {
                    Toast.makeText(this, "Permissions granted", Toast.LENGTH_SHORT).show()
                } else {
                    Toast.makeText(this, "Permissions required for eSIM activation", Toast.LENGTH_LONG).show()
                }
            }
        }
    }

    inner class WebAppInterface(private val activity: MainActivity) {
        @JavascriptInterface
        fun requestPermissions() {
            runOnUiThread { checkPermissions() }
        }

        @JavascriptInterface
        fun requestEsim() {
            if (ContextCompat.checkSelfPermission(activity, Manifest.permission.READ_PHONE_STATE) 
                == PackageManager.PERMISSION_GRANTED) {
                esimManager.requestEsim(activity)
            } else {
                runOnUiThread {
                    Toast.makeText(activity, "Please grant permissions first", Toast.LENGTH_SHORT).show()
                    checkPermissions()
                }
            }
        }
    }

    companion object {
        private const val PERMISSION_REQUEST_CODE = 123
    }
}
