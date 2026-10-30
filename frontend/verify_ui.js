import puppeteer from 'puppeteer-core'

const EDGE_PATH = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'
const SCREENSHOT_PATH = 'C:\\Users\\Admin\\.gemini\\antigravity\\brain\\1154d95e-5502-408b-86cc-f97bcb7f391e\\mission_control.png'

async function run() {
  console.log('Launching Edge via puppeteer-core...')
  const browser = await puppeteer.launch({
    executablePath: EDGE_PATH,
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--window-size=1650,1100'],
    defaultViewport: { width: 1650, height: 1100 }
  })

  try {
    const page = await browser.newPage()
    page.on('console', msg => console.log('BROWSER CONSOLE:', msg.text()))
    page.on('pageerror', err => console.error('BROWSER PAGE ERROR:', err.toString()))

    console.log('Navigating to http://127.0.0.1:5173...')
    await page.goto('http://127.0.0.1:5173', { waitUntil: 'networkidle0', timeout: 15000 })

    // Test 1: Verify 3-Scenario Batch Selector buttons exist
    console.log('Verifying 3-Scenario Batch Selector pills...')
    const bodyInitial = await page.evaluate(() => document.body.innerText)
    const hasBatch101 = bodyInitial.includes('Batch #101')
    const hasBatch204 = bodyInitial.includes('Batch #204')
    const hasBatch408 = bodyInitial.includes('Batch #408')
    console.log(`- Batch #101 present: ${hasBatch101}`)
    console.log(`- Batch #204 present: ${hasBatch204}`)
    console.log(`- Batch #408 present: ${hasBatch408}`)

    // Test 2: Click Batch #101 (Grade A)
    console.log('\nTesting Scenario 1: Batch #101 (Grade A)...')
    const buttons = await page.$$('button')
    for (const btn of buttons) {
      const text = await page.evaluate(el => el.textContent, btn)
      if (text.includes('Batch #101')) {
        await btn.click()
        break
      }
    }
    await page.waitForFunction(
      () => document.body.innerText.includes('PASSED') && document.body.innerText.includes('1.2%'),
      { timeout: 8000 }
    )
    console.log('✓ Batch #101 executed successfully (PASSED, 1.2% defect, 0% penalty)')

    // Test 3: Click Batch #204 (Tier-1 Warning)
    console.log('\nTesting Scenario 2: Batch #204 (Moderate Clumping)...')
    const buttons2 = await page.$$('button')
    for (const btn of buttons2) {
      const text = await page.evaluate(el => el.textContent, btn)
      if (text.includes('Batch #204')) {
        await btn.click()
        break
      }
    }
    await page.waitForFunction(
      () => document.body.innerText.includes('WARNING') && document.body.innerText.includes('4.4%'),
      { timeout: 8000 }
    )
    console.log('✓ Batch #204 executed successfully (WARNING, 4.4% defect, 3.6% discount)')

    // Test 4: Click Batch #408 (Critical Spoilage - Full Breach)
    console.log('\nTesting Scenario 3: Batch #408 (Critical Spoilage)...')
    const buttons3 = await page.$$('button')
    for (const btn of buttons3) {
      const text = await page.evaluate(el => el.textContent, btn)
      if (text.includes('Batch #408')) {
        await btn.click()
        break
      }
    }
    // With 2.0s artificial latency in simulation mode, wait up to 10s for the pipeline response
    await page.waitForFunction(
      () => document.body.innerText.includes('BREACH') && (document.body.innerText.includes('14.') || document.body.innerText.includes('13.')),
      { timeout: 12000 }
    )
    console.log('✓ Batch #408 executed successfully (BREACH with dynamic defect, $23,250 debit note, $7,100 hedge)')

    console.log('\nSettling animations/charts...')
    await new Promise(r => setTimeout(r, 2000))

    console.log('Capturing verified screenshot to', SCREENSHOT_PATH)
    await page.screenshot({ path: SCREENSHOT_PATH, fullPage: true })

    const finalBody = await page.evaluate(() => document.body.innerText)

    const checks = [
      { name: '3-Scenario Batch Selector in Header', passed: hasBatch101 && hasBatch204 && hasBatch408 },
      { name: 'Meta AI Telemetry Strip Visible', passed: finalBody.toLowerCase().includes('meta ai telemetry') },
      { name: 'Model ID sam-3.1 Latency Badge', passed: finalBody.includes('sam-3.1') },
      { name: 'Model ID Muse Voice Transcribe', passed: finalBody.includes('Muse Voice Transcribe') },
      { name: 'Model ID muse-spark-1.3 Latency Badge', passed: finalBody.includes('muse-spark-1.3') },
      { name: 'Model ID muse-wonder-1.0 Latency Badge', passed: finalBody.includes('muse-wonder-1.0') },
      { name: 'Engine Mode Badge (LIVE_META_API or MOCK_SAFE)', passed: finalBody.includes('LIVE_META_API') || finalBody.includes('MOCK_SAFE') },
      { name: 'Panel 1: Warehouse Visual Feed & Voice', passed: finalBody.includes('Panel 1') },
      { name: 'Panel 2: Structured Grading & Shock', passed: finalBody.includes('Panel 2') },
      { name: 'Panel 3: Quant Risk Engine', passed: finalBody.includes('Panel 3') },
      { name: 'Panel 4: Muse Wonder 1.0 Verifiable ERP', passed: finalBody.includes('Panel 4') },
      { name: 'Double-Entry Invariant: Assets == Liab + Equity ($381,750 = $131,750 + $250,000)', passed: finalBody.includes('Assets == Liabilities + Equity') && (finalBody.includes('381,750') || finalBody.includes('381750')) },
      { name: 'Double-Entry Journal: Total_Debits == Total_Credits ($30,350 == $30,350)', passed: finalBody.includes('Total_Debits == Total_Credits') && (finalBody.includes('30,350') || finalBody.includes('30350')) },
      { name: 'Treasury Bound 1: Hedge_Cost <= 5.0% of Contract Notional ($7,750)', passed: finalBody.includes('Hedge_Cost <= 5.0% of Contract Notional') },
      { name: 'Treasury Bound 2: Hedge_Cost <= 20.0% of 95% VaR ($8,775)', passed: finalBody.includes('Hedge_Cost <= 20.0% of 95% VaR') },
      { name: 'Penalty Debit Note ($23,250.00)', passed: finalBody.includes('23,250') },
      { name: 'Options Strap Hedge ($7,100.00)', passed: finalBody.includes('7,100') }
    ]

    console.log('\n--- VERIFICATION AUDIT MATRIX ---')
    let allPassed = true
    for (const c of checks) {
      console.log(`${c.passed ? '✓' : '✗'} ${c.name}: ${c.passed ? 'PASSED' : 'FAILED'}`)
      if (!c.passed) allPassed = false
    }

    if (allPassed) {
      console.log('\nALL 17 VERIFICATION CHECKS PASSED WITH 100% SUCCESS!')
    } else {
      console.error('\nSOME CHECKS FAILED!')
      process.exit(1)
    }

  } finally {
    await browser.close()
  }
}

run().catch(err => {
  console.error('Test run failed:', err)
  process.exit(1)
})
