
package com.example.testimei

import android.Manifest
import android.os.Build
import android.os.Bundle
import android.webkit.JavascriptInterface
import android.webkit.WebView
import android.webkit.WebViewClient
import androidx.appcompat.app.AppCompatActivity
import androidx.core.app.ActivityCompat

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

        webView = findViewById(R.id.webView)
        webView.settings.apply {
            javaScriptEnabled = true
            domStorageEnabled = true
            databaseEnabled = true
        }
        webView.webViewClient = WebViewClient()
        webView.addJavascriptInterface(WebAppInterface(this), "Android")
        webView.loadUrl("https://get-dot-esim.replit.app")
    }

    inner class WebAppInterface(private val activity: MainActivity) {
        @JavascriptInterface
        fun requestPermissions() {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
                ActivityCompat.requestPermissions(
                    activity,
                    arrayOf(Manifest.permission.READ_PHONE_STATE),
                    PERMISSION_REQUEST_CODE
                )
            }
        }

        @JavascriptInterface
        fun requestEsim() {
            esimManager.requestEsim(activity)
        }
    }

    companion object {
        private const val PERMISSION_REQUEST_CODE = 123
    }
}
