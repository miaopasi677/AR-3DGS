package com.example.inmo

import android.content.Intent
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Button
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import com.example.inmo.ui.theme.InmoTheme

class MainActivity : ComponentActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()

        setContent {
            InmoTheme {
                Surface(modifier = Modifier.fillMaxSize()) {
                    MainContent(modifier = Modifier.padding(16.dp))
                }
            }
        }
    }
}

@Composable
fun MainContent(modifier: Modifier = Modifier) {
    Column(
        modifier = modifier.fillMaxSize(),
        verticalArrangement = Arrangement.Center,
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        Text(text = "INMO AIR3 摄像头应用")
        
        Spacer(modifier = Modifier.height(32.dp))
        
        // 添加摄像头按钮
        val context = LocalContext.current
        Button(
            onClick = {
                val intent = Intent(context, StreamingCameraActivity::class.java)
                context.startActivity(intent)
            }
        ) {
            Text("INMO AIR3 实时视频流")
        }
    }
}

@Preview(showBackground = true)
@Composable
fun MainContentPreview() {
    InmoTheme {
        MainContent()
    }
}