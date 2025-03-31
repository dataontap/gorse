
package com.example.yourapp

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
    private val client = OkHttpClient()
    private val API_URL = "https://get-dot-esim.replit.app/api/imei"

    @SuppressLint("HardwareIds")
    fun requestEsim(context: Context) {
        if (checkPermission(context)) {
            val telephonyManager = context.getSystemService(Context.TELEPHONY_SERVICE) as TelephonyManager
            
            // Get IMEI(s)
            val imei1 = telephonyManager.getImei(0)
            val imei2 = try { telephonyManager.getImei(1) } catch (e: Exception) { null }
            
            // Create JSON payload
            val json = JSONObject()
            json.put("imei1", imei1)
            imei2?.let { json.put("imei2", it) }

            // Make API request
            val requestBody = RequestBody.create(
                MediaType.parse("application/json"), 
                json.toString()
            )
            
            val request = Request.Builder()
                .url(API_URL)
                .post(requestBody)
                .build()

            client.newCall(request).enqueue(object : Callback {
                override fun onFailure(call: Call, e: IOException) {
                    // Handle error
                }

                override fun onResponse(call: Call, response: Response) {
                    // Handle success
                }
            })
        }
    }

    private fun checkPermission(context: Context): Boolean {
        return ContextCompat.checkSelfPermission(
            context,
            Manifest.permission.READ_PHONE_STATE
        ) == PackageManager.PERMISSION_GRANTED
    }
}
