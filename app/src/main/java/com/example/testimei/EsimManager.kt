
package com.example.testimei

import android.Manifest
import android.annotation.SuppressLint
import android.content.Context
import android.content.pm.PackageManager
import android.os.Build
import android.telephony.TelephonyManager
import androidx.core.content.ContextCompat
import okhttp3.*
import okhttp3.MediaType.Companion.toMediaType
import org.json.JSONObject
import java.io.IOException

class EsimManager(private val callback: (Boolean, String) -> Unit) {
    private val client = OkHttpClient()
    private val API_URL = "https://get-dot-esim.replit.app/api/imei"

    private fun checkPermission(context: Context): Boolean {
        return ContextCompat.checkSelfPermission(
            context,
            Manifest.permission.READ_PHONE_STATE
        ) == PackageManager.PERMISSION_GRANTED
    }

    @SuppressLint("HardwareIds")
    fun requestEsim(context: Context) {
        if (!checkPermission(context)) {
            callback(false, "Permission not granted")
            return
        }

        try {
            val telephonyManager = context.getSystemService(Context.TELEPHONY_SERVICE) as TelephonyManager
            val imei1 = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                telephonyManager.getImei(0)
            } else {
                telephonyManager.deviceId
            }

            val imei2 = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                try {
                    telephonyManager.getImei(1)
                } catch (e: Exception) {
                    null
                }
            } else null

            val json = JSONObject().apply {
                put("imei1", imei1)
                imei2?.let { put("imei2", it) }
            }

            val request = Request.Builder()
                .url(API_URL)
                .post(RequestBody.create(MediaType.toMediaType("application/json"), json.toString()))
                .build()

            client.newCall(request).enqueue(object : Callback {
                override fun onFailure(call: Call, e: IOException) {
                    callback(false, "Network error: ${e.message}")
                }

                override fun onResponse(call: Call, response: Response) {
                    val responseData = response.body()?.string()
                    callback(response.isSuccessful, responseData ?: "No response data")
                }
            })
        } catch (e: Exception) {
            callback(false, "Error: ${e.message}")
        }
    }
}
