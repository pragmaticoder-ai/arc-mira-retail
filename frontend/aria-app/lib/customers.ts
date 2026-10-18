import accounts from './demoCustomers.json'
export type DemoCustomer = typeof accounts[number]
export const demoCustomers=accounts
export function findCustomer(username: string): DemoCustomer|undefined {
  const value=username.trim()
  if(value===process.env.DEMO_USERNAME)return {...accounts[0],username:value}
  return accounts.find(account=>account.username===value)
}
