package com.performer.client

import android.graphics.BitmapFactory
import android.os.Bundle
import android.widget.Button
import android.widget.EditText
import android.widget.ImageView
import androidx.appcompat.app.AppCompatActivity
import java.io.InputStream
import java.io.OutputStream
import java.net.Socket
import java.nio.ByteBuffer
import java.nio.ByteOrder

class MainActivity : AppCompatActivity() {

    private lateinit var videoView: ImageView
    private lateinit var ipInput: EditText
    private lateinit var btnConnect: Button
    private var socket: Socket? = null
    private var isConnected = false

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        videoView = findViewById(R.id.videoView)
        ipInput = findViewById(R.id.ipInput)
        btnConnect = findViewById(R.id.btnConnect)

        btnConnect.setOnClickListener {
            if (!isConnected) {
                val ip = ipInput.text.toString()
                connectToConsole(ip)
            } else {
                disconnect()
            }
        }
    }

    private fun connectToConsole(ip: String) {
        Thread {
            try {
                socket = Socket(ip, 36000)
                isConnected = true
                runOnUiThread { btnConnect.text = "Rozłącz" }

                val inputStream = socket!!.getInputStream()
                val headerBuffer = ByteArray(28)

                while (isConnected) {
                    var bytesRead = 0
                    while (bytesRead < 28) {
                        val read = inputStream.read(headerBuffer, bytesRead, 28 - bytesRead)
                        if (read == -1) break
                        bytesRead += read
                    }
                    if (bytesRead < 28) break

                    val bb = ByteBuffer.wrap(headerBuffer).order(ByteOrder.LITTLE_ENDIAN)
                    val magic = bb.int
                    val codec = bb.int
                    val size = bb.int

                    if (magic == 0x48593337) {
                        val payload = ByteArray(size)
                        var payloadRead = 0
                        while (payloadRead < size) {
                            val read = inputStream.read(payload, payloadRead, size - payloadRead)
                            if (read == -1) break
                            payloadRead += read
                        }

                        if (codec == 1) { // JPEG Video Frame
                            val bitmap = BitmapFactory.decodeByteArray(payload, 0, payload.size)
                            runOnUiThread {
                                videoView.setImageBitmap(bitmap)
                            }
                        }
                    }
                }
            } catch (e: Exception) {
                e.printStackTrace()
            } finally {
                disconnect()
            }
        }.start()
    }

    private fun disconnect() {
        isConnected = false
        try {
            socket?.close()
        } catch (e: Exception) { }
        runOnUiThread { btnConnect.text = "Połącz" }
    }
}
