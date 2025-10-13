import { fileURLToPath, URL } from 'node:url'
import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import fs from 'node:fs' 
import dotenv from 'dotenv'
dotenv.config({path: '../.env'})

export default ({ mode }) => {
  // This line loads the .env file
  process.env = {...process.env, ...loadEnv(mode, process.cwd() + '/prox_frontend', '.env')};
  return defineConfig({
    plugins: [
      vue(),
    ],
    resolve: {
      alias: {
        '@': fileURLToPath(new URL('./src', import.meta.url))
      }
    },
    server: {
    	https: { // <-- Add this entire object
        key: fs.readFileSync('./localhost-key.pem'),
        cert: fs.readFileSync('./localhost.pem'),
      },
      proxy: {
        '/api': {
          // This line uses the variable
          target: process.env.VITE_API_TARGET,
          changeOrigin: true,
          rewrite: (path) => path.replace(/^\/api/, ''),
        },
      }
    }
  })
}
