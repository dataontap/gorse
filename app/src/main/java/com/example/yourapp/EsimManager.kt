
package com.example.yourapp // Replace with your actual package name

import android.Manifest
import android.annotation.SuppressLint
import android.content.Context
import android.content.pm.PackageManager
import android.telephony.TelephonyManager
import androidx.core.content.ContextCompat
import okhttp3.*
import org.json.JSONObject
import java.io.IOException

class EsimManager {
    private val apiUrl = "https://get-dot-esim.replit.app/imei"

    @SuppressLint("HardwareIds")
    fun requestEsim(context: Context) {
        if (ContextCompat.checkSelfPermission(
                context,
                Manifest.permission.READ_PHONE_STATE
            ) != PackageManager.PERMISSION_GRANTED
        ) {
            // Handle permission request
            return
        }

        val telephonyManager = context.getSystemService(Context.TELEPHONY_SERVICE) as TelephonyManager
        
        val imei1 = telephonyManager.getImei(0)
        val imei2 = try {
            telephonyManager.getImei(1)
        } catch (e: Exception) {
            null
        }

        val payload = JSONObject().apply {
            put("imei1", imei1)
            imei2?.let { put("imei2", it) }
        }

        val client = OkHttpClient()
        val request = Request.Builder()
            .url(apiUrl)
            .post(RequestBody.create(MediaType.parse("application/json"), payload.toString()))
            .build()

        client.newCall(request).enqueue(object : Callback {
            override fun onResponse(call: Call, response: Response) {
                // Handle success
            }

            override fun onFailure(call: Call, e: IOException) {
                // Handle error
            }
        })
    }
}
