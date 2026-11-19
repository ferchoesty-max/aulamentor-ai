import { initializeApp, getApps } from 'firebase/app'
import { connectAuthEmulator, getAuth, type Auth } from 'firebase/auth'

export default defineNuxtPlugin(() => {
  const config = useRuntimeConfig().public
  const useEmulators = config.useFirebaseEmulators === 'true'

  const firebaseValues = [
    config.firebaseApiKey,
    config.firebaseAuthDomain,
    config.firebaseProjectId,
    config.firebaseAppId
  ]
  const hasExampleValue = firebaseValues.some((value) =>
    !value || /dummy|placeholder|example/i.test(value)
  )

  if (!useEmulators && hasExampleValue) {
    return { provide: { auth: null as Auth | null } }
  }

  const firebaseConfig = {
    apiKey: config.firebaseApiKey || 'demo-api-key',
    authDomain: config.firebaseAuthDomain || 'aulamentor-ai-demo.firebaseapp.com',
    projectId: config.firebaseProjectId || 'aulamentor-ai-demo',
    storageBucket: config.firebaseStorageBucket,
    messagingSenderId: config.firebaseMessagingSenderId,
    appId: config.firebaseAppId || '1:000000000000:web:demo'
  }

  const app = getApps().length ? getApps()[0] : initializeApp(firebaseConfig)
  const auth = getAuth(app)
  if (useEmulators) {
    try {
      connectAuthEmulator(auth, 'http://127.0.0.1:9099', { disableWarnings: true })
    } catch {
      // Evita reconectar en hot reload.
    }
  }
  return { provide: { auth } }
})