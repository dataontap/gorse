
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

class EsimManager(private val callback: (Boolean, String) -> Unit) {
    private val client = OkHttpClient()
    private val API_URL = "https://get-dot-esim.replit.app/api/imei"

    @SuppressLint("HardwareIds")
    fun requestEsim(context: Context) {
        // Let user choose identification method
        val builder = AlertDialog.Builder(context)
        builder.setTitle("Device Identification")
            .setMessage("eSIM activation requires device identification. How would you like to proceed?")
            .setPositiveButton("Use IMEI (Recommended)") { _, _ ->
                requestEsimWithIMEI(context)
            }
            .setNegativeButton("Use Alternative ID") { _, _ ->
                requestEsimWithoutIMEI(context)
            }
            .show()
    }

    private fun requestEsimWithIMEI(context: Context) {
        if (!checkPermission(context)) {
            callback(false, "Permission not granted")
            return
        }

        val telephonyManager = context.getSystemService(Context.TELEPHONY_SERVICE) as TelephonyManager
        
        try {
            val imei1 = telephonyManager.getImei(0)
            val imei2 = try { telephonyManager.getImei(1) } catch (e: Exception) { null }
            
            val json = JSONObject().apply {
                put("imei1", imei1)
                imei2?.let { put("imei2", it) }
            }

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
                    callback(false, "Failed to request eSIM: ${e.message}")
                }

                override fun onResponse(call: Call, response: Response) {
                    val success = response.isSuccessful
                    val message = if (success) "eSIM request successful" else "Failed to request eSIM"
                    callback(success, message)
                }
            })
        } catch (e: Exception) {
            callback(false, "Error accessing device information: ${e.message}")
        }
    }

    private fun checkPermission(context: Context): Boolean {
        return ContextCompat.checkSelfPermission(
            context,
            Manifest.permission.READ_PHONE_STATE
        ) == PackageManager.PERMISSION_GRANTED
    }
}
