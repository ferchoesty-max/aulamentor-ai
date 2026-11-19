import { initializeApp, getApps } from 'firebase/app'
import { getAuth, type Auth } from 'firebase/auth'

export default defineNuxtPlugin(() => {
  const config = useRuntimeConfig().public

  const firebaseValues = [
    config.firebaseApiKey,
    config.firebaseAuthDomain,
    config.firebaseProjectId,
    config.firebaseAppId
  ]
  const hasExampleValue = firebaseValues.some((value) =>
    !value || /dummy|placeholder|example/i.test(value)
  )

  if (hasExampleValue) {
    return { provide: { auth: null as Auth | null } }
  }

  const firebaseConfig = {
    apiKey: config.firebaseApiKey,
    authDomain: config.firebaseAuthDomain,
    projectId: config.firebaseProjectId,
    storageBucket: config.firebaseStorageBucket,
    messagingSenderId: config.firebaseMessagingSenderId,
    appId: config.firebaseAppId
  }

  const app = getApps().length ? getApps()[0] : initializeApp(firebaseConfig)
  return { provide: { auth: getAuth(app) } }
})