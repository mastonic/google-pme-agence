import { OrderButton } from '../../components/OrderButton'
import type { FePack } from './packs'

/** Lien de paiement direct si configuré, sinon formulaire de commande de la boutique. */
export function BuyButton({ pack, label = 'Acheter', className = 'btn btn-primary', style }: { pack: FePack; label?: string; className?: string; style?: React.CSSProperties }) {
  if (pack.checkoutUrl) {
    return <a href={pack.checkoutUrl} className={className} style={{ textAlign: 'center', ...style }} rel="nofollow">{label}</a>
  }
  return (
    <OrderButton product={`${pack.name} (${pack.price} € HT)`} title={`Commander : ${pack.name}`} phoneRequired={false}
      intro="Indiquez votre email : vous recevez le lien de paiement et de téléchargement, avec votre facture."
      className={className} style={style}>
      {label}
    </OrderButton>
  )
}
